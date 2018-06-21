from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

STATIC_FOLDER = '../ui/build'
TESTING = True
# Prevent Flask-Login from disabling itself due to TESTING being set
LOGIN_DISABLED = False
MONGO_TEST_METHOD = 'live'
SECRET_KEY = 'vpfocnbpienbpirpvbnps'
DATABASE = {
    'name': 'test.db',
    'engine': 'peewee.SqliteDatabase'
}

BCRYPT_LOG_ROUNDS = 4
