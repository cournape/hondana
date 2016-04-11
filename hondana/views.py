""" Cornice services.
"""
from __future__ import absolute_import

import os.path
import textwrap

import flask
import jinja2
import six

from .app import app
from .config import Configuration
from .models import Project, ProjectsManager


STORE_PREFIX = os.path.abspath(".store")
CONFIG = Configuration(STORE_PREFIX)
CONFIG.validate()

_PROJECTS_MANAGER = ProjectsManager.from_directory(CONFIG.projects_prefix)


def version_path(name, version):
    return os.path.join(CONFIG.projects_prefix, name, version)


@app.route('/')
def root():
    return flask.redirect(flask.url_for("projects"))


@app.route('/projects/')
def projects():
    projects = [
        (project, project.name) for project in _PROJECTS_MANAGER.get_projects()
    ]
    return flask.render_template("projects.html", projects=projects)


@app.route('/projects/<name>/')
def project(name):
    project = _PROJECTS_MANAGER.get_project(name)
    versions = [
        (version, "/projects/" + project.name + "/" + version)
        for version in sorted(project.versions)
    ]
    return flask.render_template("project.html", project=project, versions=versions)


@app.route('/projects/<name>/<version>/')
def version(name, version):
    project = _PROJECTS_MANAGER.get_project(name)
    assert version in project.versions

    doc_path = version_path(name, version)
    doc_relpath = os.path.relpath(doc_path, STORE_PREFIX)
    redirect_path = os.path.join("/docs-static", doc_relpath)
    response = flask.make_response()
    response.headers['X-Accel-Redirect'] = redirect_path
    return response
