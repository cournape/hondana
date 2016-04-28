import logging
import os
import os.path

import flask

from .config import Configuration
from .models import ProjectsMetadataManager


_PROJECTS_PREFIX = "HONDANA_PROJECTS_PREFIX"
_BACKUPS_PREFIX = "HONDANA_BACKUPS_PREFIX"
_STORE_PREFIX = "HONDANA_STORE_PREFIX"


def app_factory():
    store_prefix = os.path.abspath(".store")

    config_path = os.environ.get("HONDANA_CONFIG")
    if config_path is None:
        config_path = "config.yaml"

    config = Configuration.from_path(config_path)
    config.validate()

    app = flask.Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key
    app.config[_PROJECTS_PREFIX] = config.projects_prefix
    app.config[_STORE_PREFIX] = config.store_prefix
    app.config[_BACKUPS_PREFIX] = config.backups_prefix

    return app


app = app_factory()

def projects_prefix(app):
    return app.config[_PROJECTS_PREFIX]


def store_prefix(app):
    return app.config[_STORE_PREFIX]


def backups_prefix(app):
    return app.config[_BACKUPS_PREFIX]


@app.before_request
def before_request():
    flask.g.projects_metadata = ProjectsMetadataManager.from_directory(
        app.config[_PROJECTS_PREFIX]
    )

@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)


from . import views
