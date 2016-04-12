import redis


PROJECT_ID_KEY = "next_project_id"
PROJECTS_KEY = "projects"
VERSIONS_KEY_TEMPLATE = "versions:{}"

_GET_OR_CREATE_SCRIPT = """\
local project_id = nil

if redis.call("HEXISTS", KEYS[2], ARGV[1]) == 1 then
    project_id = redis.call("HGET", KEYS[2], ARGV[1])
else
    project_id = redis.call("INCR", KEYS[1])
    redis.call("HSET", KEYS[2], ARGV[1], project_id)
end

return project_id
"""


class MetadataStore(object):
    """ Redis-backed metadata store.

    While it is racy, the hope is that the design allows internal consistency.

    The schema is straighforward:

        1. a integer key 'next_project_id' containing the next available
           project id
        2. a hash 'projects' mapping <project name> to <project id>
        3. a per-project hash 'versions:<project id>' mapping <version> to
           <blob id>
    """
    def __init__(self, cx):
        self._cx = cx
        self._get_or_create_project_id_script = cx.register_script(
            _GET_OR_CREATE_SCRIPT
        )

    def get_blob_id(self, project_name, version):
        project_id = self._get_project_id(project_name)
        if project_id is not None:
            versions_key = self._version_key(project_id)
            blob_id = self._cx.hget(versions_key, version)
            if blob_id is None:
                raise ValueError("No such version: {!r}".format(version))
            return blob_id
        else:
            raise ValueError("No such project: {!r}".format(project_name))

    def get_project_names(self):
        """ Get the list of all the project names."""
        return self._cx.hkeys(PROJECTS_KEY)

    def get_versions(self, project_name):
        """ Get the list of all the versions for the given project name.

        If the project is not registered, an empty list is returned
        """
        project_id = self._cx.hget(PROJECTS_KEY, project_name)
        return self._cx.hkeys(self._version_key(project_id))

    def has_project(self, project_name):
        """ Return True if the given project name is registered.
        """
        return self._cx.hexists(PROJECTS_KEY, project_name)

    def has_version(self, project_name, version):
        """ Return True if the given version is registered for that project.
        """
        project_id = self._get_project_id(project_name)
        if project_id is not None:
            versions_key = self._version_key(project_id)
            return self._cx.hexists(versions_key, version)
        else:
            return False

    def register_version(self, project_name, version, blob_id):
        """ Register the blob id to the given version for the given project

        Parameters
        ----------
        project_name : str
            The project name
        version : str
            The project version
        blob_id : str
            The blob id for the corresponding doc storage
        """
        project_id = self._get_or_create_project_id(project_name)
        versions_key = self._version_key(project_id)
        self._cx.hset(versions_key, version, blob_id)

    def unregister_project(self, project_name):
        """ Unregister the given project."""
        if self.has_project(project_name):
            project_id = self._get_or_create_project_id(project_name)
            version_key = self._version_key(project_id)
            self._cx.hdel(PROJECTS_KEY, project_name)
            self._cx.delete(version_key)

    def unregister_version(self, project_name, version):
        """ Unregister the given version for that project."""
        if self.has_project(project_name):
            project_id = self._get_or_create_project_id(project_name)
            versions_key = self._version_key(project_id)
            self._cx.hdel(versions_key, version)

    def _get_project_id(self, project_name):
        return self._cx.hget(PROJECTS_KEY, project_name)

    def _get_or_create_project_id(self, project_name):
        return self._get_or_create_project_id_script(
            keys=[PROJECT_ID_KEY, PROJECTS_KEY],
            args=[project_name]
        )

    def _version_key(self, project_id):
        return VERSIONS_KEY_TEMPLATE.format(project_id)
