import os.path

import flask

from .config import Configuration
from .models import ProjectsMetadataManager


_PROJECTS_PREFIX = "HONDANA_PROJECTS_PREFIX"
_STORE_PREFIX = "HONDANA_STORE_PREFIX"


def app_factory():
    store_prefix = os.path.abspath(".store")

    config = Configuration(store_prefix, "a super secret")
    config.validate()

    app = flask.Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key
    app.config[_PROJECTS_PREFIX] = config.projects_prefix
    app.config[_STORE_PREFIX] = config.store_prefix

    return app


app = app_factory()


@app.before_request
def before_request():
    flask.g.projects_metadata = ProjectsMetadataManager.from_directory(
        app.config[_PROJECTS_PREFIX]
    )


def projects_prefix(app):
    return app.config[_PROJECTS_PREFIX]


def store_prefix(app):
    return app.config[_STORE_PREFIX]
