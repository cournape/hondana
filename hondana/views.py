""" Cornice services.
"""
from __future__ import absolute_import

import os.path
import textwrap

import flask
import jinja2
import six

from .app import app
from .models import Project
from .utils import makedirs


STORE_PREFIX = os.path.abspath(".store")
# We don't makedirs that one to avoid silently storing them somehwere
# unexpected
assert os.path.exists(STORE_PREFIX)

PROJECTS_PREFIX = os.path.join(STORE_PREFIX, "docs", "projects")
makedirs(PROJECTS_PREFIX)


PROJECTS_TEMPLATE = jinja2.Template("""
<!DOCTYPE html>
<html>
<body>

<h1>Projects</h1>

{% block body %}
    <ul>
    {% for project, link in projects %}
    <li><a href={{ link }}>{{ project.name }}</a></li>
    {% endfor %}
    </ul>
{% endblock %}

</body>
</html>
""")


PROJECT_TEMPLATE = jinja2.Template("""
<!DOCTYPE html>
<html>
<body>

<h1>{{ project.name }}</h1>

{% block body %}
    <ul>
    {% for version, link in versions %}
    <li><a href={{ link }}>{{version }}</a></li>
    {% endfor %}
    </ul>
{% endblock %}

</body>
</html>
""")


def project_path(name):
    return os.path.join(PROJECTS_PREFIX, name)


def version_path(name, version):
    return os.path.join(project_path(name), version)


_PROJECTS = {}
for name in os.listdir(PROJECTS_PREFIX):
    versions = os.listdir(project_path(name))
    _PROJECTS[name] = Project(name.decode(), versions)


def list_projects():
    return list(six.iterkeys(_PROJECTS))


def list_versions(name):
    project = _PROJECTS.get(self.request.matchdict['name'])
    assert project is not None
    return list(project.versions)


@app.route('/')
def projects():
    projects = [
        (project, project.name)
        for project in six.itervalues(_PROJECTS)
    ]
    return PROJECTS_TEMPLATE.render(projects=projects)


@app.route('/<name>/')
def project(name):
    assert name in _PROJECTS
    project = _PROJECTS[name]
    versions = [
        (version, project.name + "/" + version)
        for version in project.versions
    ]
    return PROJECT_TEMPLATE.render(project=project, versions=versions)


@app.route('/<name>/<version>/')
def version(name, version):
    assert name in _PROJECTS
    project = _PROJECTS[name]
    assert version in project.versions

    doc_path = version_path(name, version)
    doc_relpath = os.path.relpath(doc_path, STORE_PREFIX)
    redirect_path = os.path.join("/static", doc_relpath)
    response = flask.make_response()
    response.headers['X-Accel-Redirect'] = redirect_path
    return response
