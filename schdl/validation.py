# Copyright 2013 Fourth Rune, LLC
# Licensed under the MIT license - http://opensource.org/licenses/MIT
"""Validate Schdl data update objects.

Can be used as a library or a command-line tool. The only requirements are
Python 2.7 and the validictory library.

Usage:
python validation.py < foo.json
python validation.py foo.json bar.json

Errors are printed to stderr. Exit status is 0 if input is valid, 1 if one or
more errors were encountered.
"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import collections
import json
import sys

import validictory


def merge(*dicts):
    out = dict()
    for _dict in dicts:
        out.update(_dict)
    return out


def nullable(*types):
    return {'type': list(types + (NULL,))}


def required(schema):
    return merge(schema, REQUIRED)


def optional(schema):
    return merge(schema, OPTIONAL)


REQUIRED = {'required': True}
OPTIONAL = {'required': False}
NULL = {'type': 'null'}

STD_STRING = {
    'type': 'string',
    'minLength': 1,
    'maxLength': 255,
    'pattern': r'\A[^\n\t]*\Z',  # No newlines or tabs allowed
}

REQD_STD_STRING = required(STD_STRING)

NONNEGATIVE_INT = {
    'type': 'integer',
    'minimum': 0,
}

MINUTES = {
    'type': 'integer',
    'minimum': 0,
    'maximum': 1440,
}

METADATA_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'format': required({
            'type': 'integer',
            'enum': [1],
        }),
        'strategy': required({
            'type': 'string',
            'enum': ['full_terms'],
        }),
        'terms': required({
            'type': 'array',
            'minItems': 1,
            'maxItems': 50,
            'uniqueItems': True,
            'items': STD_STRING
        }),
    },
}

SNAPSHOT_METADATA_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'format': required({
            'type': 'integer',
            'enum': [1],
        }),
        'strategy': required({
            'type': 'string',
            'enum': ['snapshot'],
        }),
    },
}

REQUIREMENT_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'type': required({'enum': ['requirement']}),
        'id': REQD_STD_STRING,
        'short': STD_STRING,
        'long': STD_STRING,
    },
}

INSTRUCTOR_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'type': required({'enum': ['instructor']}),
        'id': REQD_STD_STRING,
        'first': nullable(STD_STRING),
        'middle': nullable(STD_STRING),
        'last': STD_STRING,
        'email': nullable(STD_STRING),
    },
}

TERM_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'type': required({'enum': ['term']}),
        'id': REQD_STD_STRING,
        'name': STD_STRING,
        'start': {
            'format': 'date',
        },
        'end': {
            'format': 'date',
        },
    },
}

SUBJECT_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'type': required({'enum': ['subject']}),
        'id': REQD_STD_STRING,
        'term': STD_STRING,
        'name': STD_STRING,
        'abbreviation': STD_STRING,
        'segments': {
            'type': 'array',
            'maxItems': 25,
            'uniqueItems': True,
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'id': REQD_STD_STRING,
                    'name': REQD_STD_STRING,
                },
            },
        },
    },
}

COURSE_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'type': required({'enum': ['course']}),
        'id': REQD_STD_STRING,
        'term': STD_STRING,
        'code': STD_STRING,
        'name': STD_STRING,
        'continuity_id': nullable(STD_STRING),
        'description': {
            'type': 'string',
            'maxLength': 8192,
            'blank': True,
        },
        'credits': nullable({
            'type': 'number',
            'minimum': 0,
        }),
        'independent_study': {
            'type': 'boolean',
        },
        'subjects': {
            'type': 'array',
            'minItems': 1,
            'maxItems': 15,
            'uniqueItems': True,
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'id': REQD_STD_STRING,
                    'segment': optional(STD_STRING),
                }
            },
        },
        'requirements': {
            'type': 'array',
            'maxItems': 10,
            'uniqueItems': True,
            'items': STD_STRING
        },
    },
}

SECTION_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'type': required({'enum': ['section']}),
        'id': REQD_STD_STRING,
        'course': STD_STRING,
        'section': STD_STRING,
        'details': {
            'type': 'string',
            'maxLength': 4096,
            'blank': True,
        },
        'status': {
            'type': 'string',
            'enum': ['open', 'closed', 'restricted', 'closed_restricted'],
        },
        'status_text': STD_STRING,
        'enrolled': nullable(NONNEGATIVE_INT),
        'waiting': nullable(NONNEGATIVE_INT),
        'limit': nullable(NONNEGATIVE_INT),
        'instructors': {
            'type': 'array',
            'maxLength': 10,
            'uniqueItems': True,
            'items': STD_STRING,
        },
        'times': {
            'type': 'array',
            'maxLength': 10,
            'uniqueItems': True,
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'start': MINUTES,
                    'end': MINUTES,
                    'days': {
                        'type': 'array',
                        'uniqueItems': True,
                        'minItems': 1,
                        'items': {
                            'type': 'string',
                            'enum': ['su', 'm', 'tu', 'w', 'th', 'f', 'sa'],
                        },
                    },
                    'type': optional(nullable(STD_STRING)),
                    'building': optional(nullable(STD_STRING)),
                    'room': optional(nullable(STD_STRING)),
                },
            },
        },
    },
}

SCHEMATA = {
    'requirement': REQUIREMENT_SCHEMA,
    'instructor': INSTRUCTOR_SCHEMA,
    'term': TERM_SCHEMA,
    'subject': SUBJECT_SCHEMA,
    'course': COURSE_SCHEMA,
    'section': SECTION_SCHEMA,
}

OBJ_SCHEMA = {
    'type': 'object',
    'properties': {
        'type': required({
            'enum': list(SCHEMATA),
        }),
        'id': REQD_STD_STRING,
    },
}


def Validate(obj):
    validictory.validate(obj, OBJ_SCHEMA)
    schema = SCHEMATA[obj['type']]
    validictory.validate(obj, schema)


def ValidateMetadata(obj):
    validictory.validate(obj, METADATA_SCHEMA)


def ValidateSnapshotMetadata(obj):
    validictory.validate(obj, SNAPSHOT_METADATA_SCHEMA)


def main(files):
    valid = True
    if files:
        for fname in files:
            with open(fname) as fobj:
                valid &= _processFile(fname, fobj)
    else:
        valid &= _processFile('<stdin>', sys.stdin)
    sys.exit(0 if valid else 1)


def _processFile(fname, fobj):
    valid = True
    try:
        ValidateMetadata(json.loads(fobj.readline()))
    except ValueError as e:
        valid = False
        sys.stderr.write('%s:1 %s\n' % (fname, e))
    updates = collections.defaultdict(dict)
    for lineno, line in enumerate(fobj, 2):
        try:
            obj = json.loads(line)
            Validate(obj)
            if obj['id'] in updates[obj['type']]:
                raise ValueError(
                    'Object with type %s and id %s already seen at line %s'
                    % (obj['type'], obj['id'], updates[obj['type']][obj['id']])
                )
            updates[obj['type']][obj['id']] = lineno
        except ValueError as e:
            valid = False
            sys.stderr.write('%s:%s %s\n' % (fname, lineno, e))
    return valid

if __name__ == '__main__':
    main(sys.argv[1:])
