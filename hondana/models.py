import os

import six

from attr import attributes, attr
from attr.validators import instance_of


@attributes
class Project(object):
    name = attr(validator=instance_of(six.string_types))
    versions = attr(validator=instance_of(list))


class ProjectsManager(object):
    @classmethod
    def from_directory(cls, directory):
        projects = []
        for name in os.listdir(directory):
            project_directory = os.path.join(directory, name)
            versions = os.listdir(project_directory)
            projects.append(Project(name, versions))
        return cls(projects)

    def __init__(self, projects):
        self._projects = {}
        for project in projects:
            self._projects[project.name] = project

    def add_project(self, name, version):
        if not self.has_project(name):
            project = Project(name, [version])
            self._projects[project.name] = project
        else:
            project = self.get_project(name)
            if not version in project.versions:
                project.versions.append(version)

    def get_project(self, name):
        if self.has_project(name):
            return self._projects[name]
        else:
            raise ValueError("No such project: {!r}".format(name))

    def get_projects(self):
        return list(self._projects[k] for k in sorted(self._projects))

    def has_project(self, name):
        return name in self._projects

    def has_version(self, name, version):
        if self.has_project(name):
            project = self.get_project(name)
            return version in project.versions
        else:
            return False
