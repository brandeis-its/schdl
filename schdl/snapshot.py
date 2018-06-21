from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import json

from schdl import mongo
from schdl import util
from schdl import validation

JSON_ARGS = util.JSON_ARGS


def get_projection(type):
    schema = validation.SCHEMATA[type]
    keys = set(schema['properties'].keys())
    keys.remove('type')
    return util.Projection(keys, _id=False)

PROJECTIONS = {type: get_projection(type) for type in mongo.types}


def generate_snapshot(c, out):
    format = {
        'format': 1,
        'strategy': 'snapshot',
    }
    json.dump(format, out, **JSON_ARGS)
    out.write('\n')
    for type in mongo.types:
        if type not in mongo.subdocument:
            _dump_type(c, out, type)


def _dump_type(c, out, type):
    projection = PROJECTIONS[type].mongo()
    if type in mongo.has_subdocument:
        subdocument_type = mongo.has_subdocument[type]
        subdocument_key = subdocument_type + 's'
        subdocument_projection = PROJECTIONS[subdocument_type]
        projection[subdocument_key] = True
        for obj in c[type].find({}, projection):
            out_obj = obj.copy()
            del out_obj[subdocument_key]
            out_obj['type'] = type
            json.dump(out_obj, out, **JSON_ARGS)
            out.write('\n')
            for subobj in obj[subdocument_key]:
                subobj = subdocument_projection(subobj)
                subobj['type'] = subdocument_type
                subobj[type] = obj['id']
                json.dump(subobj, out, **JSON_ARGS)
                out.write('\n')
    else:
        for obj in c[type].find({}, projection):
            obj['type'] = type
            json.dump(obj, out, **JSON_ARGS)
            out.write('\n')
