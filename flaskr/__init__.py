import os
from flask import Flask

def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        #set SECRET_KEY in the environment when deployed, otherwise anyone can forge a session and reset their attempts
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        #the scraper writes test.db in the project root
        DATABASE=os.environ.get('DATABASE', os.path.join(os.path.dirname(app.root_path), 'test.db')),
        #YYYY-MM-DD, pretend it is this day (for testing the daily rotation)
        FORCE_DAY=os.environ.get('FORCE_DAY'),
    )
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    if not app.debug and not app.testing:
        #production: a guessable key would let anyone forge a session and reset their attempts
        if app.config['SECRET_KEY'] == 'dev':
            raise RuntimeError('Set the SECRET_KEY environment variable (or run with --debug for local testing).')
        app.config.update(
            SESSION_COOKIE_SECURE=True,  # the site is served over https only
            SESSION_COOKIE_SAMESITE='Lax',
            SEND_FILE_MAX_AGE_DEFAULT=7 * 24 * 3600,  # champion images and logos rarely change
        )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    from . import db, answer
    db.init_app(app)
    app.register_blueprint(answer.bp)

    return app
