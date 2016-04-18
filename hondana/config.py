import os.path

import six
import yaml

from attr import attributes, attr
from attr.validators import instance_of

from .utils import makedirs


@attributes
class Configuration(object):
    store_prefix = attr(validator=instance_of(six.string_types))
    secret_key = attr(validator=instance_of(six.string_types))

    @classmethod
    def from_path(cls, path):
        with open(path, "rt") as fp:
            data = yaml.safe_load(fp)

        store_prefix = data["store_prefix"]
        secret = data["secret"]
        return cls(store_prefix, secret)

    @property
    def projects_prefix(self):
        return os.path.join(self.store_prefix, "docs", "projects")

    def validate(self):
        # We don't makedirs that one to avoid silently storing them somehwere
        # unexpected
        assert os.path.exists(self.store_prefix)
        makedirs(self.projects_prefix)
