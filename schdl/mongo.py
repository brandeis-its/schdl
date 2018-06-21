from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import pymongo

from schdl import app

INDICES = (
    ('schools', [('fragment', pymongo.ASCENDING)], {'unique': True}),
    ('schools', [('hostname', pymongo.ASCENDING)], {'unique': True}),
    ('users', [('email', pymongo.ASCENDING)], {'unique': True}),
    ('users', [('secret', pymongo.ASCENDING)], {'unique': True}),
    ('users', [('schedules.secret', pymongo.ASCENDING)],
     {'unique': True, 'sparse': True}),
    ('instructors', [('id', pymongo.ASCENDING)], {'unique': True}),
    ('instructors', [('fragment', pymongo.ASCENDING)], {'unique': True}),
    ('instructors', [('email', pymongo.ASCENDING)], {}),
    ('terms', [('id', pymongo.ASCENDING)], {'unique': True}),
    ('terms', [('fragment', pymongo.ASCENDING)], {'unique': True}),
    ('requirements', [('id', pymongo.ASCENDING)], {'unique': True}),
    ('terms', [('subjects.id', pymongo.ASCENDING)],
     {'unique': True, 'sparse': True}),
    ('terms', [('id', pymongo.ASCENDING),
               ('subjects.fragment', pymongo.ASCENDING)],
     {'unique': True, 'sparse': True}),
    ('courses', [('id', pymongo.ASCENDING)], {'unique': True}),
    ('courses', [('term', pymongo.ASCENDING), ('fragment', pymongo.ASCENDING)],
     {'unique': True}),
    ('courses', [('sections.id', pymongo.ASCENDING)],
     {'unique': True, 'sparse': True}),
    ('courses', [('code', pymongo.ASCENDING)], {}),
    ('courses', [('name', pymongo.ASCENDING)], {}),
    ('courses', [('continuity_id', pymongo.ASCENDING)], {}),
    ('courses', [('subjects.id', pymongo.ASCENDING)], {}),
    ('courses', [('requirements.id', pymongo.ASCENDING)], {}),
    ('email_verifications', [('secret', pymongo.ASCENDING)], {'unique': True}),
    ('data_updates', [('active', pymongo.ASCENDING)], {'unique': True, 'sparse': True}),
)
SHARED_COLLECTIONS = ('schools')

types = ('instructor', 'term', 'requirement', 'subject', 'course', 'section')
fragment_fields = dict(instructor=('first', 'middle', 'last'),
                       term=('name',),
                       subject=('abbreviation',),
                       course=('code',))
fragment_unique = dict(instructor=(),
                       term=(),
                       subject=(),
                       course=('term',))
subdocument = dict(subject='term',
                   section='course')
has_subdocument = {v: k for k, v in subdocument.iteritems()}


def EnsureIndices(shared=True, school_fragment=True):
    """Call mongo's ensure_index to make sure DB is properly indexed.

    Args:
        shared:
            If truthy, ensure indices for collections shared among all
            schools (see SHARED_COLLECTIONS).
        school_fragment:
            If True, ensure indices for all school-spefic collections for all
            schools. If None, do not ensure indices for school-specific
            collections. Otherwise, must be a school fragment and only call
            ensure_index for that school's collections.
    """
    if school_fragment is True:
        schools = [school['fragment'] for school in
                   app.mongo.db.schools.find({},
                                             {'fragment': True, '_id': False})
                   ]
    elif school_fragment is not None:
        schools = [school_fragment]
    for collection, fields, options in INDICES:
        if collection in SHARED_COLLECTIONS:
            if shared:
                app.mongo.db[collection].ensure_index(fields, **options)
        elif schools:
            for school in schools:
                collection = '%s.%s' % (school, collection)
                app.mongo.db[collection].ensure_index(fields, **options)


class SchoolCollections(object):
    def __init__(self, school_fragment):
        parent = app.mongo.db[school_fragment]
        self.school_fragment = school_fragment
        self.user = parent.users
        self.instructor = parent.instructors
        self.term = parent.terms
        self.requirement = parent.requirements
        self.course = parent.courses
        self.data_update = parent.data_updates
        self.email_verification = parent.email_verifications
        # Subdocument types
        self.subject = self.term
        self.section = self.course

    def __getitem__(self, item):
        return getattr(self, item)
