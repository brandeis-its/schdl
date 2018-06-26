from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import datetime
import logging
import logging.handlers
import os

import flask
import flask_mail
import jinja2

from flask.ext import pymongo
from flask.ext import bcrypt
from flask.ext import login

logging.basicConfig(level='INFO')

LOGGER = logging.getLogger(__name__)


# Workaround http://bugs.python.org/issue7980
datetime.datetime.strptime('', '')


class FlaskMailHandler(logging.Handler):
    def __init__(self, recipients, mailer, **kwargs):
        super(FlaskMailHandler, self).__init__(**kwargs)
        self.recipients = recipients
        self.mailer = mailer

    def emit(self, record):
        msg = self.format(record)
        subj = self.getSubject(record, msg)
        email = flask_mail.Message(
            subj,
            recipients=self.recipients,
        )
        email.body = 'User-agent: %s\n\n%s' % (
            flask.request.headers.get('User-agent'),
            msg
        )
        self.mailer.send(email)

    def getSubject(self, record, msg):
        first_line = msg.split('\n')[0]
        host = flask.request.headers.get('Host')
        if host:
            return '%s: %s (%s)' % (record.levelname, first_line[:70], host)
        else:
            return '%s: %s' % (record.levelname, first_line[:70])


app = flask.Flask(__name__,
                  static_folder='ui',
                  static_url_path='/static')

@app.before_request
def before_request():
    if flask.request.url.endswith('/readiness_check'):
        return
    if flask.request.url.endswith('/liveness_check'):
        return
    # TODO: Fix this before enabling it
    if app.config.get('FORCE_SSL') and not flask.request.is_secure:
        url = flask.request.url.replace('http://', 'https://', 1)
        return flask.redirect(url, code=301)

# First, try to create the symlink
try:
    if not os.path.isdir(app.static_folder):
        os.symlink('../wsgi/static', app.static_folder)
except OSError:
    pass
if not os.path.isdir(app.static_folder):
    raise IOError('Static folder is missing!')

app.login_manager = login.LoginManager()
app.mail = flask_mail.Mail()

app.config.from_object('schdl.baseconfig')
app.config.from_pyfile('../schdl.cfg')
if 'MONGO_TEST_METHOD' in app.config:
    app.mongo = None
else:
    app.mongo = pymongo.PyMongo(app)
app.bcrypt = bcrypt.Bcrypt(app)
app.login_manager.init_app(app)
app.mail.init_app(app)

if app.config.get('LOG_TO_EMAIL_ENABLED'):
    handler = FlaskMailHandler(app.config['LOG_TO_EMAIL_RECIPIENTS'],
                               app.mail,
                               level=logging.ERROR)
    # Apply handler to root logger
    logging.getLogger().addHandler(handler)


class MyLoader(jinja2.BaseLoader):
    def __init__(self, loader):
        super(MyLoader, self).__init__()
        self.loader = loader

    def get_source(self, env, tmpl):
        if tmpl.startswith('/static'):
            tmpl = 'generated/app/' + tmpl[8:]
            return self.loader.get_source(env, tmpl)


app.jinja_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    MyLoader(app.jinja_loader)
])


@app.errorhandler(404)
def page_not_found(e):
    return flask.jsonify(dict(status=404)), 404


@app.errorhandler(500)
def internal_server_error(e):
    return flask.jsonify(dict(status=500)), 500
