import unittest
import uuid

import redis
import six
import testing.redis

from ..metadata_store import MetadataStore


class TestMetadataStore(unittest.TestCase):
    def setUp(self):
        self.redis_server = testing.redis.RedisServer()
        self.r = redis.Redis(**self.redis_server.dsn())

    def tearDown(self):
        self.redis_server.stop()

    def test_empty(self):
        # Given
        store = MetadataStore(self.r)

        # When
        projects = store.get_project_names()

        # Then
        self.assertEqual(projects, [])
        self.assertFalse(store.has_project("foo"))

        # When/Then
        with self.assertRaises(ValueError):
            store.get_blob_id("foo", "1.0.0")
        with self.assertRaises(ValueError):
            store.get_blob_id("bar", "1.0.0")

    def test_register_version(self):
        # Given
        store = MetadataStore(self.r)
        name = "traits"
        version = "v4.0.0"
        blob_id = uuid.uuid4().hex

        # When
        store.register_version(name, version, blob_id)

        # Then
        projects = store.get_project_names()
        versions = store.get_versions(name)
        self.assertEqual(projects, [name])
        self.assertEqual(versions, [version])

        self.assertIs(store.has_project(name), True)
        self.assertIs(store.has_project(name + ".bak"), False)
        self.assertIs(store.has_version(name, version), True)
        self.assertIs(store.has_version(name, version + ".0"), False)
        self.assertIs(store.has_version(name  + ".bak", version), False)

        self.assertEqual(store.get_blob_id(name, version), blob_id)

        # Given
        blob_id = uuid.uuid4().hex

        # When
        store.register_version(name, version, blob_id)

        # Then
        self.assertEqual(store.get_blob_id(name, version), blob_id)

    def test_unregister(self):
        # Given
        store = MetadataStore(self.r)
        name1 = "traits"
        name2 = "traitsui"

        version1_1 = "v4.0.0"
        blob_id1_1 = uuid.uuid4().hex
        version1_2 = "v5.0.0"
        blob_id1_2 = uuid.uuid4().hex

        version2_1 = "v1.0.0"
        blob_id2_1 = uuid.uuid4().hex
        version2_2 = "v2.0.0"
        blob_id2_2 = uuid.uuid4().hex

        # When
        store.register_version(name1, version1_1, blob_id1_1)
        store.register_version(name1, version1_2, blob_id1_2)
        store.register_version(name2, version2_1, blob_id2_1)
        store.register_version(name2, version2_2, blob_id2_2)

        # Then
        six.assertCountEqual(self, store.get_project_names(), [name1, name2])
        six.assertCountEqual(
            self, store.get_versions(name1), [version1_1, version1_2]
        )
        six.assertCountEqual(
            self, store.get_versions(name2), [version2_1, version2_2]
        )

        # When
        store.unregister_version(name1, version1_1)
        store.unregister_project(name2)

        # Then
        six.assertCountEqual(self, store.get_project_names(), [name1])
        six.assertCountEqual(
            self, store.get_versions(name1), [version1_2]
        )
        self.assertIs(store.has_project(name2), False)
        self.assertEqual(store.get_versions(name2), [])
