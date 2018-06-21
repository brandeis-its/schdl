from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import collections
import contextlib
import datetime
import io
import json
import logging
import re
import tempfile

import bson
import flask
import flask_mail
import pymongo

import schdl
import schdl.snapshot
from schdl import app
from schdl import mongo
from schdl import storage
from schdl import util
from schdl import validation

LOGGER = logging.getLogger(__name__)

UPLOAD_UPDATE = '00/upload_update'
QUEUED = '09/queued'
CLAIMED = '10/claimed'
DOWNLOAD_SNAPSHOT = '20/download_snapshot'
DOWNLOAD_UPDATE = '30/download_update'
READ_UPDATE = '40/read_update'
READ_SNAPSHOT = '50/read_snapshot'
DIFF = '60/diff'
UPLOAD_DIFF = '70/upload_diff'
UPDATE_SNAPSHOT = '80/update_snapshot'
UPLOAD_SNAPSHOT = '85/upload_snapshot'
APPLY_CHANGES = '90/apply_changes'
FAILED = '97/failed'
FAILED_TO_APPLY = '98/failed_to_apply'
COMPLETE = '99/complete'
COMPLETE_NO_CHANGES = '99/complete_no_changes'

FRAGMENT_UNSAFE = re.compile(r'[^a-zA-Z0-9]+')

JSON_ARGS = util.JSON_ARGS

routes = util.RouteSet()


class Error(Exception):
    pass


class AlreadyUpdating(Error):
    pass


class ParentDNE(Error):
    pass


def load_obj(line):
    obj = json.loads(line)
    validation.Validate(obj)
    type_ = obj['type']
    _id = obj['id']
    del obj['type'], obj['id']
    return type_, _id, obj


def _diff_objs(old, new):
    diff = {
        'action': 'update',
        'old': {},
        'new': {},
    }
    for key, value in old.iteritems():
        if key in new:
            if type(value) is list:
                if sorted(value) != sorted(new[key]):
                    diff['old'][key] = value
                    diff['new'][key] = new[key]
            elif value != new[key]:
                diff['old'][key] = value
                diff['new'][key] = new[key]
        else:
            diff['old'][key] = value
    for key, value in new.iteritems():
        if key not in old:
            diff['new'][key] = value
    if not (diff['old'] or diff['new']):
        diff = None
    return diff


def apply_changes(changes, c):
    errors = []
    stop = False
    for type_ in mongo.types:
        for id_, change in changes[type_].iteritems():
            try:
                apply_change(type_, id_, change, c)
            except (ParentDNE, pymongo.errors.PyMongoError) as e:
                errors.append('%s(%s): %s: %s' % (type_, id_, type(e), e))
            except Exception as e:
                errors.append('%s(%s): %s: %s' % (type_, id_, type(e), e))
                stop = True
                break
        if stop:
            break
    if errors:
        raise IOError('\n'.join(errors))


def apply_change(type_, _id, change, c):
    if 'derived' in change:
        change['new'].update(change['derived'])
        del change['derived']
    new = change.get('new', {})
    collection = c[type_]
    if change['action'] == 'create' and type_ in mongo.fragment_fields:
        assign_fragment(type_, _id, new, collection)
    # Sections are stored as subdocuments of course, subjects are subdocuments
    # of term.
    if type_ in mongo.subdocument:
        apply_subdocument_change(c, type_, _id, change)
    elif change['action'] == 'delete':
        collection.remove({'id': _id}, w=1)
    elif change['action'] == 'create':
        new_obj = new.copy()
        new_obj['id'] = _id
        collection.insert(new_obj, w=1)
    else:
        collection.update({'id': _id}, {'$set': new}, w=1)


def apply_subdocument_change(c, type_, _id, change):
    parent_type = mongo.subdocument[type_]
    collection = c[parent_type]
    if change['action'] == 'delete':
        # If deleting a section, remove it from all schedules first
        if type_ == 'section':
            c.user.update(
                {
                    'schedules.sections.id': _id
                }, {
                    '$pull': {'schedules.$.sections': {'id': _id}}
                },
                multi=True,
            )
        parent = change['old'][parent_type]
        collection.update({type_ + 's.id': _id},
                          {'$pull': {type_ + 's': {'id': _id}}},
                          w=1)
    else:
        new = change['new']
        parent = new.pop(parent_type, None)
        if change['action'] == 'create':
            new_obj = new.copy()
            new_obj['id'] = _id
            result = collection.update({'id': parent},
                                       {'$push': {type_ + 's': new_obj}},
                                       w=1)
            if not result['updatedExisting']:
                raise ParentDNE('type=%s, id=%s, %s=%s'
                                % (type_, _id, parent_type, parent))
        else:
            # TODO(eitan): what if parent document changed? we need to fetch
            # the old one, delete it from old parent, apply updates locally,
            # and add it to its new parent (or just ban reparenting)
            assert parent is None
            result = collection.update(
                {type_ + 's.id': _id},
                {
                    '$set': {type_ + 's.$.' + key: val
                             for key, val in new.iteritems()}
                },
                w=1,
            )
            if not result['updatedExisting']:
                raise ParentDNE('type=%s, id=%s, %s=%s'
                                % (type_, _id, parent_type, parent))


def assign_fragment(type_, _id, obj, collection):
    fragment = ' '.join([obj[field]
                        for field in mongo.fragment_fields[type_]
                        if field in obj and obj[field]])
    fragment = FRAGMENT_UNSAFE.sub('_', fragment).strip('_')
    if type_ in mongo.subdocument:
        fragment_field = type_ + 's.fragment'
    else:
        fragment_field = 'fragment'
    fragment_query = {fragment_field: fragment}
    if type_ in mongo.subdocument:
        fragment_query['id'] = obj[mongo.subdocument[type_]]
    for field in mongo.fragment_unique[type_]:
        fragment_query[field] = obj[field]
    if collection.find_one(fragment_query, []):
        i = 2
        fragment_query[fragment_field] += '_2'
        while collection.find_one(fragment_query, []):
            i += 1
            fragment_query[fragment_field] = fragment + '_' + unicode(i)
        fragment = fragment_query[fragment_field]
    obj['fragment'] = fragment


def update_name(update_or_id):
    if isinstance(update_or_id, bson.objectid.ObjectId):
        _id = update_or_id
    else:
        _id = update_or_id['_id']
    return '%s_%s' % (_id.generation_time.isoformat(b'T').replace('+', 'Z'),
                      _id)


def _upload_update_file(school, update_or_id, file_type, file):
    file.seek(0)
    return storage.upload(
        file,
        '%s/%s/%s.json' % (school['fragment'],
                           update_name(update_or_id),
                           file_type),
        'application/json',
    )


def add_update(school, update_file, c):
    _id = c.data_update.insert({
        'status': UPLOAD_UPDATE,
        'last_modified': datetime.datetime.utcnow(),
    })
    LOGGER.info('Update %s: %s', update_name(_id), UPLOAD_UPDATE)
    _upload_update_file(school, _id, 'update', update_file)
    _set_update_status(c, _id, QUEUED)
    return _id


@contextlib.contextmanager
def claim_update(c, school):
    try:
        update = c.data_update.find_and_modify(
            query={'status': QUEUED},
            update={'$set': {
                'status': CLAIMED,
                'active': True,
                'last_modified': datetime.datetime.utcnow(),
            }},
            new=True,
            sort={'_id': pymongo.ASCENDING},
            w=1,
        )
    except (pymongo.errors.DuplicateKeyError,
            pymongo.errors.OperationFailure) as e:
        # See https://jira.mongodb.org/browse/PYTHON-592 - OperationFailure is
        # raised instead of DuplicateKeyError
        if (isinstance(e, pymongo.errors.DuplicateKeyError)
            or (isinstance(e, pymongo.errors.OperationFailure)
                and ('E11000' in e.message or 'E11001' in e.message))):
            active = c.data_update.find_one({'active': True},
                                            {'last_modified': True})
            if (
                active
                and (datetime.datetime.utcnow()
                     - active['last_modified'].replace(tzinfo=None)
                     > datetime.timedelta(0.0416667))
                and datetime.datetime.utcnow().minute % 5 == 0
               ):
                LOGGER.error('Active update is more than an hour stale!')
            update = None
        else:
            raise
    if update is None:
        yield None
    else:
        LOGGER.info('Update %s: %s', update_name(update), CLAIMED)
        try:
            yield update
        except Exception as e:
            _unclaim_update(c, school, update, FAILED, error=e)
            raise


def _unclaim_update(c, school, update, newstatus,
                    error=None, has_snapshot=False):
    LOGGER.info('Update %s: %s', update_name(update), newstatus)
    oldstatus = update['status']
    operation = {
        '$set': {
            'status': newstatus,
            'last_modified': datetime.datetime.utcnow(),
        },
        '$unset': {'active': ''},
    }
    if has_snapshot:
        operation['$set']['has_snapshot'] = True
    if error:
        operation['$set']['has_errors'] = True
    c.data_update.update(
        {'_id': update['_id']},
        operation,
        w=1,
    )
    update['status'] = newstatus
    if error:
        error = unicode(error)
        _send_failure_emails(c, school, update, oldstatus, error)
        with tempfile.TemporaryFile() as error_file:
            error_file.write(error)
            error_file.write('\n')
            _upload_update_file(school, update, 'error', error_file)


def _set_update_status(c, update, newstatus):
    LOGGER.info('Update %s: %s', update_name(update), newstatus)
    if isinstance(update, bson.objectid.ObjectId):
        _id = update
    else:
        update['status'] = newstatus
        _id = update['_id']
    return c.data_update.update(
        {'_id': _id},
        {
            '$set': {
                'status': newstatus,
                'last_modified': datetime.datetime.utcnow(),
            },
        },
        w=1,
    )


def _add_update_stats(c, update, same, new, updated, deleted):
    stats = {
        'same': same,
        'new': new,
        'updated': updated,
        'deleted': deleted,
    }
    if isinstance(update, bson.objectid.ObjectId):
        _id = update
    else:
        _id = update['_id']
        update['diff_stats'] = stats
    return c.data_update.update(
        {'_id': _id},
        {
            '$set': {
                'diff_stats': stats,
            },
        },
        w=1,
    )


# Returns a file-like object of the latest snapshot file
def get_latest_snapshot(school, c, update):
    cursor = c.data_update.find(
        {'$or': [{'has_snapshot': True},
                 {'active': True}],
         '_id': {'$ne': update['_id']}}
    ).sort('_id', pymongo.DESCENDING).limit(1)
    latest = list(cursor)
    if latest:
        latest = latest[0]
    else:
        return None
    if latest.get('active'):
        raise AlreadyUpdating(unicode(latest['_id']))
    tmp = tempfile.TemporaryFile()
    storage.download(tmp,
                     '%s/%s/snapshot.json' % (school['fragment'],
                                              update_name(latest)))
    tmp.seek(0)
    return tmp


def process_update(school, c):
    with claim_update(c, school) as update:
        if not update:
            return None
        _set_update_status(c, update, DOWNLOAD_SNAPSHOT)
        snapshot_file = get_latest_snapshot(school, c, update)
        # If this is the first update, create a fake empty snapshot file
        if snapshot_file is None:
            snapshot_file = io.BytesIO(b'{"format":1,"strategy":"snapshot"}\n')
        _set_update_status(c, update, DOWNLOAD_UPDATE)
        with tempfile.TemporaryFile() as update_file:
            storage.download(
                update_file,
                '%s/%s/update.json' % (school['fragment'],
                                       update_name(update)))
            update_file.seek(0)
            _set_update_status(c, update, READ_UPDATE)
            meta, updates = read_updates(update_file)
        terms = set(meta['terms'])
        _set_update_status(c, update, READ_SNAPSHOT)
        snapshot = read_snapshot(snapshot_file, updates)
        _set_update_status(c, update, DIFF)
        changes, new, same, updated = diff(snapshot, updates)
        snapshot_file.seek(0)
        deleted = add_deletes_for_terms(terms, snapshot_file, updates, changes)
        _add_update_stats(c, update, same, new, updated, deleted)
        if max(new, updated, deleted) == 0:
            _unclaim_update(c, school, update, COMPLETE_NO_CHANGES)
            return new, updated, same, deleted
        _set_update_status(c, update, UPLOAD_DIFF)
        with tempfile.TemporaryFile() as diff_file:
            write_diff(diff_file, changes)
            _upload_update_file(school, update, 'diff', diff_file)
        snapshot_file.seek(0)
        _set_update_status(c, update, UPDATE_SNAPSHOT)
        with tempfile.TemporaryFile() as new_snapshot_file:
            patch_snapshot(snapshot_file, changes, new_snapshot_file)
            snapshot_file.close()
            _set_update_status(c, update, UPLOAD_SNAPSHOT)
            _upload_update_file(school, update, 'snapshot', new_snapshot_file)
        _set_update_status(c, update, APPLY_CHANGES)
    # Let go of claim_update context manager and handle exceptions manually
    try:
        apply_changes(changes, c)
        _unclaim_update(c, school, update, COMPLETE, has_snapshot=True)
    except Exception as e:
        with tempfile.TemporaryFile() as new_snapshot_file:
            schdl.snapshot.generate_snapshot(c, new_snapshot_file)
            _upload_update_file(school, update, 'snapshot', new_snapshot_file)
        _unclaim_update(c, school, update, FAILED_TO_APPLY,
                        error=e, has_snapshot=True)
        raise
    finally:
        for term in terms:
            update_subjects_shown(term, c)
    # TODO(eitan): Add update status to update obj instead of returning it
    return new, updated, same, deleted


def read_updates(input_file):
    updates = collections.defaultdict(dict)
    # Don't catch metadata validation errors; raise immediately
    meta = json.loads(input_file.readline())
    validation.ValidateMetadata(meta)
    # Collect all validation errors instead of raising at the first one
    errors = []
    for lineno, line in enumerate(input_file, 2):
        try:
            type_, _id, obj = load_obj(line)
            if _id in updates[type_]:
                raise ValueError('%s[%s] already seen'
                                 % (type_, _id))
            updates[type_][_id] = obj
        except ValueError as e:
            errors.append('%s: %s: %s' % (lineno, type(e), e))
    if errors:
        raise ValueError('\n'.join(errors))
    return meta, updates


def read_snapshot(snapshot_file, updates):
    meta = json.loads(snapshot_file.readline())
    validation.ValidateSnapshotMetadata(meta)
    snapshot = collections.defaultdict(dict)
    for lineno, line in enumerate(snapshot_file, 1):
        try:
            type_, _id, obj = load_obj(line)
        except Exception as e:
            fmt = e.args[0] + ' at line %s'
            args = e.args[1:] + (lineno,)
            print(fmt % args)
            e.args = ()
            raise
        if _id in updates[type_]:
            snapshot[type_][_id] = obj
    return snapshot


def diff(snapshot, updates):
    new = same = update = 0
    changes = collections.defaultdict(dict)
    for type_ in mongo.types:
        for _id, obj in updates[type_].iteritems():
            if _id in snapshot[type_]:
                change = _diff_objs(snapshot[type_][_id], obj)
                if change:
                    update += 1
                    _add_derived(type_, change, snapshot[type_][_id])
                    changes[type_][_id] = change
                else:
                    same += 1
            else:
                new += 1
                change = {
                    'action': 'create',
                    'new': obj,
                }
                _add_derived(type_, change, None)
                changes[type_][_id] = change
    # TODO(eitan): referential integrity check
    return changes, new, same, update


def _add_derived(type_, change, old):
    new = change['new']
    if old is None:
        complete = new
    else:
        complete = old.copy()
        complete.update(new)
    is_create = change['action'] == 'create'
    derived = {}
    if type_ == 'instructor':
        if 'first' in new or 'middle' in new or 'last' in new:
            name = util.name({field: complete[field]
                              for field in ('first', 'middle', 'last')})
            derived['name'] = name
            derived['searchable_name'] = util.make_searchable(name)
    elif type_ == 'course':
        if is_create:
            derived['sections'] = []
        if 'name' in new:
            derived['searchable_name'] = util.make_searchable(new['name'])
        if 'code' in new:
            derived['searchable_code'] = util.make_searchable(new['code'])
        if 'description' in new:
            derived['searchable_description'] = util.make_searchable(
                new['description'])
    elif type_ == 'section':
        if 'details' in new:
            derived['searchable_details'] = util.make_searchable(
                new['details'])
    elif type_ == 'term' and is_create:
        derived['subjects'] = []
    elif type_ == 'subject':
        if 'name' in new:
            derived['searchable_name'] = util.make_searchable(new['name'])
        if 'abbreviation' in new:
            derived['searchable_abbreviation'] = util.make_searchable(
                new['abbreviation'])
    if derived:
        change['derived'] = derived
        return True
    else:
        return False


def add_deletes_for_terms(terms, snapshot_file, updates, changes):
    deletes = 0
    # Discard metadata
    snapshot_file.readline()
    courses = set()
    for line in snapshot_file:
        type_, _id, obj = load_obj(line)
        if type_ in ('course', 'subject') and obj['term'] in terms:
            if type_ == 'course':
                courses.add(_id)
            if _id not in updates[type_]:
                deletes += 1
                changes[type_][_id] = {
                    'action': 'delete',
                    'old': obj,
                }
    # Scan through the snapshot again to find sections, since they only
    # reference a term indirectly by way of their course.
    snapshot_file.seek(0)
    # Discard metadata again
    snapshot_file.readline()
    for line in snapshot_file:
        type_, _id, obj = load_obj(line)
        if (type_ == 'section'
                and _id not in updates['section']
                and obj['course'] in courses):
            deletes += 1
            changes['section'][_id] = {
                'action': 'delete',
                'old': obj,
            }
    return deletes


def write_diff(diff_file, changes):
    heading = {
        'format': 1,
        'strategy': 'diff',
    }
    json.dump(heading, diff_file, **JSON_ARGS)
    diff_file.write('\n')
    for type_ in mongo.types:
        for _id, change in changes[type_].iteritems():
            copy = change.copy()
            copy['type'] = type_
            copy['id'] = _id
            copy.pop('derived', None)
            json.dump(copy, diff_file, **JSON_ARGS)
            diff_file.write('\n')


def patch_snapshot(old_file, patch, new_file):
    old_meta = json.loads(old_file.readline())
    assert old_meta == {'format': 1, 'strategy': 'snapshot'}
    new_meta = {
        'format': 1,
        'strategy': 'snapshot',
    }
    json.dump(new_meta, new_file, **JSON_ARGS)
    new_file.write('\n')
    for line in old_file:
        type_, _id, obj = load_obj(line)
        if _id in patch[type_]:
            change = patch[type_][_id]
            if change['action'] == 'delete':
                continue
            elif change['action'] == 'create':
                raise ValueError('Cannot create object that already exists'
                                 ' (type="%s", id="%s")'
                                 % (type_, _id))
            else:
                assert change['action'] == 'update'
                obj.update(change['new'])
                obj['type'] = type_
                obj['id'] = _id
                json.dump(obj, new_file, **JSON_ARGS)
                new_file.write('\n')
        else:
            # Object is unchanged - copy as-is
            new_file.write(line)
    # Find new objects
    for type_ in mongo.types:
        for _id, change in patch[type_].iteritems():
            if change['action'] != 'create':
                continue
            new_obj = change['new'].copy()
            new_obj['type'] = type_
            new_obj['id'] = _id
            json.dump(new_obj, new_file, **JSON_ARGS)
            new_file.write('\n')


def update_subjects_shown(term_id, c):
    term = c.term.find_one({'id': term_id})
    if not term['subjects']:
        return
    subjects_with_courses = set(c.course.find({
        'term': term_id,
        'sections.0': {'$exists': 1},
    }).distinct('subjects.id'))
    term_has_courses = bool(subjects_with_courses)
    update = {}
    if term.get('hasCourses') != term_has_courses:
        update['hasCourses'] = term_has_courses
    for i, subject in enumerate(term['subjects']):
        has_courses = subject['id'] in subjects_with_courses
        if subject.get('hasCourses') != has_courses:
            update['subjects.%s.hasCourses' % i] = has_courses
    if update:
        c.term.update({'_id': term['_id']}, {'$set': update})


@routes.add('/api/updates/<school>', methods=['POST'])
def push_update(school):
    school_fragment = school
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school_fragment},
        {'_id': False})
    c = mongo.SchoolCollections(school_fragment)
    try:
        api_key = flask.request.form['api_key']
    except KeyError:
        return flask.jsonify(reason='no_api_key'), 403
    if not app.bcrypt.check_password_hash(school['api_key_hash'], api_key):
        return flask.jsonify(reason='unrecognized_api_key'), 403
    if 'update' not in flask.request.files:
        return flask.jsonify(reason='update_missing'), 400
    _id = add_update(school,
                     flask.request.files['update'],
                     c)
    return flask.jsonify(id=unicode(_id), status='ok')


@routes.add('/api/import_update/<school>')
def import_update(school):
    if flask.request.headers.get('X-Appengine-Cron') != 'true':
        return flask.jsonify(reason='permission_denied'), 403
    school_fragment = school
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school_fragment})
    c = mongo.SchoolCollections(school_fragment)
    results = process_update(school, c)
    if results is not None:
        LOGGER.info('%s new, %s updates, %s same, %s deletes', *results)
    return flask.jsonify(status='ok')


def _send_failure_emails(c, school, update, oldstatus, error):
    msg = flask_mail.Message(
        '%s update failed' % school['hostname'][0],
        recipients=school['failure_emails'],
    )
    msg.body = flask.render_template(
        'email/update_failure_email.txt',
        school=school,
        update=update,
        failed_stage=oldstatus,
        error=error,
    )
    app.mail.send(msg)
