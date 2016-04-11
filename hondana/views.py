""" Cornice services.
"""
from __future__ import absolute_import

import os.path
import textwrap

import flask
import jinja2
import six

from .app import app
from .models import Project, ProjectsManager
from .utils import makedirs


STORE_PREFIX = os.path.abspath(".store")
# We don't makedirs that one to avoid silently storing them somehwere
# unexpected
assert os.path.exists(STORE_PREFIX)

PROJECTS_PREFIX = os.path.join(STORE_PREFIX, "docs", "projects")
makedirs(PROJECTS_PREFIX)

_PROJECTS_MANAGER = ProjectsManager.from_directory(PROJECTS_PREFIX)


def version_path(name, version):
    return os.path.join(PROJECTS_PREFIX, name, version)


@app.route('/')
def projects():
    projects = [
        (project, project.name) for project in _PROJECTS_MANAGER.get_projects()
    ]
    return flask.render_template("projects.html", projects=projects)


@app.route('/<name>/')
def project(name):
    project = _PROJECTS_MANAGER.get_project(name)
    versions = [
        (version, "/" + project.name + "/" + version)
        for version in sorted(project.versions)
    ]
    return flask.render_template("project.html", project=project, versions=versions)


@app.route('/<name>/<version>/')
def version(name, version):
    project = _PROJECTS_MANAGER.get_project(name)
    assert version in project.versions

    doc_path = version_path(name, version)
    doc_relpath = os.path.relpath(doc_path, STORE_PREFIX)
    redirect_path = os.path.join("/docs-static", doc_relpath)
    response = flask.make_response()
    response.headers['X-Accel-Redirect'] = redirect_path
    return response
