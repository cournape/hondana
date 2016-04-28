# What is hondana

Hondana (bookshelf in Japanese) is a small web application to serve sphinx
documentations. It is *not* a replacement for readthedocs.org, as it only
serves sphinx documentations (it does not build them).

The main purpose of hondana is to internally serve a bunch of projects'
documentation inside an internal network. Absolutely no security or access
control is provided.

## Features

* serve multiple versions of projects with sphinx documentation
* simple API to upload sphinx documentation from curl
* simplistic: to make deployment and maintenance easier, we try to avoid
  relying on a database

## Deployment

See [docker instructions](Docker.md) for a simple deployment using docker.

## Uploading documentation

A documentation file is expected to follow the format `<project
name>-<version>.zip`. The zipfile is expected to contain the top index.html at
its root. E.g. for a typical sphinx build:

  ``` bash
  # Build sphinx doc, assumed to be in doc/
  $ (cd doc && make html)
  $ (cd doc/build/html && zip -r ../../../foo-v0.1.0.zip)
  ```

Uploading it may be done through curl as follows:

  ``` bash
  $ curl -F "upload=@foo-v0.1.0.zip" http://host/api/v0/json/upload
  ```
