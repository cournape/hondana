""" Cornice services.
"""
from __future__ import absolute_import, print_function

import contextlib
import os.path
import re
import uuid

import flask
import flask.views
import redis
import werkzeug
import zipfile

from .app import app
from .config import Configuration
from .metadata_store import MetadataStore
from .utils import rm_rf, tempdir


_DOCZIP_R = re.compile("^([^-]+)-(.+).zip$")


STORE_PREFIX = os.path.abspath(".store")
CONFIG = Configuration(STORE_PREFIX, "a super secret")
CONFIG.validate()
app.config["SECRET_KEY"] = CONFIG.secret_key


def compute_blob_path(blob_id):
    return os.path.join(CONFIG.projects_prefix, blob_id[:2], blob_id[2:])


def _backup_if_necessary(metadata_store, name, version):
    try:
        blob_id = metadata_store.get_blob_id(name, version)
    except ValueError:
        backup = None
    else:
        blob_path = compute_blob_path(blob_id)
        backup = blob_path + ".bak"
        os.rename(blob_path, backup)

    return backup


def unzip_doc(config, upload, name, version):
    # The principle:
    # 1. If the name, version pair is already registered, we move aside the
    #    target directory as backup
    # 2. We compute a new uuid, from which we compute a unique path where we
    #    extract the newly uploaded zipfile. The uuid means the target
    #    directory is very unlikely to collide with an existing doc directory
    # 3. If some reason 2. fails, we restore the backup
    with _metadata_store(config) as metadata_store:
        backup = _backup_if_necessary(metadata_store, name, version)

        blob_id = uuid.uuid4().hex
        target_directory = compute_blob_path(blob_id)

        try:
            with tempdir() as d:
                zipfile_path = os.path.join(d, "doc.zip")
                upload.save(zipfile_path)
                with zipfile.ZipFile(zipfile_path) as zp:
                    zp.extractall(target_directory)
                metadata_store.register_version(name, version, blob_id)
        except Exception:
            rm_rf(target_directory)
            if backup is not None:
                backup_target = os.path.splitext(backup)[0]
                os.rename(backup, backup_target)
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

        unzip_doc(CONFIG, upload, name, version)

        return "", 204
    else:
        return "Invalid request format", 400


class ProjectsAPI(flask.views.MethodView):
    def get(self, project_name, version):
        with _metadata_store(CONFIG) as metadata_store:
            if project_name is None:
                project_names = metadata_store.get_project_names()
                return flask.jsonify({"projects": project_names})
            else:
                if metadata_store.has_project(project_name):
                    versions = metadata_store.get_versions(project_name)
                    return flask.jsonify(
                        {"name": project_name, "versions": versions}
                    )
                else:
                    return flask.jsonify({"error": "no such project"}), 404

    def delete(self, project_name, version):
        with _metadata_store(CONFIG) as metadata_store:
            if metadata_store.has_project(project_name):
                if version is None:
                    metadata_store.unregister_project(project_name)
                else:
                    if metadata_store.has_version(project_name, version):
                        blob_id = metadata_store.get_blob_id(
                            project_name, version
                        )
                        metadata_store.unregister_version(
                            project_name, version
                        )
                        rm_rf(compute_blob_path(blob_id))
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
    with _metadata_store(CONFIG) as metadata_store:
        projects = [
            (project_name, project_name)
            for project_name in sorted(metadata_store.get_project_names())
        ]
    return flask.render_template("projects.html", projects=projects)


@app.route('/projects/<name>/')
def project(name):
    with _metadata_store(CONFIG) as metadata_store:
        if not metadata_store.has_project(name):
            return "", 404

        versions = [
            (version, "/projects/" + name + "/" + version)
            for version in sorted(metadata_store.get_versions(name))
        ]

    return flask.render_template(
        "project.html", project=project, versions=versions
    )


@app.route('/projects/<name>/<version>/')
def version(name, version):
    with _metadata_store(CONFIG) as metadata_store:
        try:
            blob_id = metadata_store.get_blob_id(name, version)
        except ValueError:
            return "", 404

        doc_path = compute_blob_path(blob_id)

    doc_relpath = os.path.relpath(doc_path, STORE_PREFIX)
    redirect_path = os.path.join("/docs-static", doc_relpath)
    response = flask.make_response()
    response.headers['X-Accel-Redirect'] = redirect_path
    return response


@contextlib.contextmanager
def _metadata_store(config):
    cx = redis.StrictRedis(
        host=config.redis_host, port=config.redis_port, db=config.redis_db
    )
    yield MetadataStore(cx)
