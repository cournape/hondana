What is hondana
===============

Hondana (bookshelf in Japanese) is a small web application to serve sphinx
documentations. It is *not* a replacement for readthedocs.org, as it only
serves sphinx documentations (it does not build them).

The main purpose of readthedocs is to internally serve a bunch of projects'
documentation inside an internal network. Absolutely no security or access
control is provided.

Features
--------

* serve multiple versions of projects with sphinx documentation
* simple API to upload sphinx documentation from curl
* simplistic: to make deployment and maintenance easier, we try to avoid
  relying on a database

Deployment
==========

See Docker.rst for a simple deployment using docker.
