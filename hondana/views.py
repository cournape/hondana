""" Cornice services.
"""
from __future__ import absolute_import, print_function

import os.path
import re
import textwrap

import flask
import jinja2
import six
import werkzeug
import zipfile

from .app import app
from .config import Configuration
from .models import Project, ProjectsManager
from .utils import rm_rf, tempdir


_DOCZIP_R = re.compile("^([^-]+)-(.+).zip$")


STORE_PREFIX = os.path.abspath(".store")
CONFIG = Configuration(STORE_PREFIX, "a super secret")
CONFIG.validate()
app.config["SECRET_KEY"] = CONFIG.secret_key

_PROJECTS_MANAGER = ProjectsManager.from_directory(CONFIG.projects_prefix)


def version_path(name, version):
    return os.path.join(CONFIG.projects_prefix, name, version)


def unzip_doc(config, projects_manager, upload, name, version):
    target_directory = version_path(name, version)

    if projects_manager.has_version(name, version):
        backup = target_directory + ".bak"
        os.rename(target_directory, backup)
    else:
        backup = None

    try:
        with tempdir() as d:
	    zipfile_path = os.path.join(d, "doc.zip")
            upload.save(zipfile_path)
            with zipfile.ZipFile(zipfile_path) as zp:
                zp.extractall(target_directory)
        projects_manager.add_project(name, version)
    except Exception:
        rm_rf(target_directory)
        if backup is not None:
            os.rename(backup, target_directory)
        raise


# API routes
@app.route("/api/v0/json/upload", methods=["POST"])
def upload():
    files = flask.request.files
    if "upload" in files:
        upload = files["upload"]

        filename = werkzeug.secure_filename(upload.filename)
        if not filename.endswith(".zip"):
            return "Invalid request format", 400

        m = _DOCZIP_R.search(filename)
        if m is None:
            return "Invalid zip format: expected '<name>-<version>.zip'"

        name = m.groups()[0]
        version = m.groups()[1]

        unzip_doc(CONFIG, _PROJECTS_MANAGER, upload, name, version)

        return "", 204
    else:
        return "Invalid request format", 400


# WEB routes
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
