import contextlib
import errno
import os
import shutil
import tempfile


def makedirs(d):
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    try:
        yield d
    finally:
        shutil.rmtree(d)


def rm_rf(d):
    if os.path.exists(d):
        shutil.rmtree(d)
