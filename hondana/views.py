""" Cornice services.
"""
from __future__ import absolute_import, print_function

import os.path
import re
import textwrap
import uuid

import flask
import flask.views
import jinja2
import six
import werkzeug
import zipfile

from .app import app, projects_prefix, store_prefix
from .models import Project, ProjectsMetadataManager
from .utils import rm_rf, tempdir


_DOCZIP_R = re.compile("^([^-]+)-(.+).zip$")


def project_path(name):
    return os.path.join(projects_prefix(app), name)


def version_path(name, version):
    return os.path.join(project_path(name), version)


def _backup_if_required(projects_manager, name, version):
    if projects_manager.has_version(name, version):
        backup = target_directory + ".bak"
        os.rename(target_directory, backup)
    else:
        backup = None

    return backup


def unzip_doc(projects_manager, upload, name, version):
    target_directory = version_path(name, version)

    blob_id = uuid.uuid4().hex
    extract_dir = os.path.join(os.path.dirname(target_directory), blob_id)

    backup = _backup_if_required(projects_manager, name, version)

    try:
        with tempdir() as d:
            zipfile_path = os.path.join(d, "doc.zip")
            upload.save(zipfile_path)
            with zipfile.ZipFile(zipfile_path) as zp:
                zp.extractall(extract_dir)
        os.rename(extract_dir, target_directory)
        projects_manager.add_project(name, version)
    except Exception:
        rm_rf(extract_dir)
        rm_rf(target_directory)
        if backup is not None:
            os.rename(backup, target_directory)
        raise


# API routes
_API_ROOT = "/api/v0/json"

@app.route(_API_ROOT + "/upload", methods=["POST"])
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

        unzip_doc(flask.g.projects_metadata, upload, name, version)

        return "", 204
    else:
        return "Invalid request format", 400


class ProjectsAPI(flask.views.MethodView):
    def get(self, project_name, version):
        projects_metadata = flask.g.projects_metadata
        if project_name is None:
            project_names = [project.name for project in projects_metadata.get_projects()]
            return flask.jsonify({"projects": project_names})
        else:
            if projects_metadata.has_project(project_name):
                project = projects_metadata.get_project(project_name)
                return flask.jsonify({"name": project_name, "versions": project.versions})
            else:
                return flask.jsonify({"error": "no such project"}), 404

    def delete(self, project_name, version):
        projects_metadata = flask.g.projects_metadata
        if projects_metadata.has_project(project_name):
            if version is None:
                rm_rf(project_path(project_name))
                projects_metadata.delete_project(project_name)
            else:
                if _projects_metadata_manager.has_version(project_name, version):
                    rm_rf(version_path(project_name, version))
                    _projects_metadata_manager.delete_version(project_name, version)
                else:
                    return flask.jsonify({"error": "no such version"}), 404
            return "", 204
        else:
            return flask.jsonify({"error": "no such project"}), 404


projects_view = ProjectsAPI.as_view("api_projects")
app.add_url_rule(
    _API_ROOT + '/projects/', defaults={"project_name": None, "version": None},
    view_func=projects_view, methods=["GET"])
app.add_url_rule(
    _API_ROOT + '/projects/<project_name>', defaults={"version": None},
    view_func=projects_view, methods=["GET", "DELETE"])
app.add_url_rule(
    _API_ROOT + '/projects/<project_name>/<version>',
    view_func=projects_view, methods=["DELETE"])


# WEB routes
@app.route('/')
def root():
    return flask.redirect(flask.url_for("projects"))


@app.route('/projects/')
def projects():
    project_names = [
        project.name for project in flask.g.projects_metadata.get_projects()
    ]
    return flask.render_template("projects.html", project_names=project_names)


@app.route('/projects/<name>/')
def project(name):
    project = flask.g.projects_metadata.get_project(name)
    versions = sorted(project.versions)
    return flask.render_template("project.html", project=project, versions=versions)


@app.route('/projects/<name>/<version>/')
def version(name, version):
    project = flask.g.projects_metadata.get_project(name)
    assert version in project.versions

    doc_path = version_path(name, version)
    doc_relpath = os.path.relpath(doc_path, store_prefix(app))
    redirect_path = os.path.join("/docs-static", doc_relpath)
    response = flask.make_response()
    response.headers['X-Accel-Redirect'] = redirect_path
    return response
