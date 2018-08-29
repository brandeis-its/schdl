from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

STATIC_FOLDER = '../ui/build'
TESTING = True
# Prevent Flask-Login from disabling itself due to TESTING being set
LOGIN_DISABLED = False
SECRET_KEY = 'vpfocnbpienbpirpvbnps'

BCRYPT_LOG_ROUNDS = 4
