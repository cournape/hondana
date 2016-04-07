import six

from attr import attributes, attr
from attr.validators import instance_of


@attributes
class Project(object):
    name = attr(validator=instance_of(six.text_type))
    versions = attr(validator=instance_of(list))
