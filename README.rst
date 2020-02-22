===========================
Welcome to django-csvexport
===========================

Description
===========
Django-csvexport is a simple django-admin-action, that allows you to export a
selection of the fields of your model as csv-formatted data.

Features
========
* selectable model-fields
* inclusive of related models (with 1 level depth)
* customizable csv-format
* view or download csv-data

Django
======
csvformat was developed with django-2.2. Probably it works with other
django-versions (1.11 to 2.2).

Installation
============
Download or clone the repository and add csvexport to your installed apps::

    INSTALLED_APPS = [
        'csvexport',
        ...
    ]


Todo
====
* Implement a test-suite and setup continuous integration with travis.
