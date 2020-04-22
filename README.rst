=================================
Welcome to django-admin-csvexport
=================================

.. image:: https://travis-ci.com/thomst/django-admin-csvexport.svg?branch=master
   :target: https://travis-ci.com/thomst/django-admin-csvexport

.. image:: https://coveralls.io/repos/github/thomst/django-admin-csvexport/badge.svg?branch=master
   :target: https://coveralls.io/github/thomst/django-admin-csvexport?branch=master

.. image:: https://img.shields.io/badge/python-3.4%20%7C%203.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue
   :target: https://img.shields.io/badge/python-3.4%20%7C%203.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue
   :alt: python: 3.4, 3.5, 3.6, 3.7, 3.8

.. image:: https://img.shields.io/badge/django-1.11%20%7C%202.0%20%7C%202.1%20%7C%202.2%20%7C%203.0-orange
   :target: https://img.shields.io/badge/django-1.11%20%7C%202.0%20%7C%202.1%20%7C%202.2%20%7C%203.0-orange
   :alt: django: 1.11, 2.0, 2.1, 2.2, 3.0


Description
===========
Django-admin-csvexport is a django-admin-action, that allows you to export the
items of your django-admin changelist as csv-formatted data.


Features
========
* selectable model-fields
* related models included
* customizable csv-format
* view or download csv-data


Installation
============
Install from pypi.org::

    pip install django-admin-csvexport

Add csvexport to your installed apps::

    INSTALLED_APPS = [
        'csvexport',
        ...
    ]

Add csvexport to the actions of your modeladmin::

    from csvexport.actions import csvexport

    class MyModelAdmin(admin.ModelAdmin):
        ...
        actions = [csvexport]


Configuration
=============
The following settings determine the depth of the model references and the
value to display for empty fields::

    CSV_EXPORT_REFERENCE_DEPTH = 3
    CSV_EXPORT_EMPTY_VALUE = ''

Those settings define the csv-format to be used. The default values meet the
unix standard csv-format::

    CSV_EXPORT_DELIMITER = ','
    CSV_EXPORT_ESCAPECHAR = ''
    CSV_EXPORT_QUOTECHAR = '"'
    CSV_EXPORT_DOUBLEQUOTE = True
    CSV_EXPORT_LINETERMINATOR = r'\n'

(Use a raw-string for newline escape sequences.)

Per default the csv-format can be adjusted by a formular when generating the
csv-file. Set the following setting to False to not render such form::

    CSV_EXPORT_FORMAT_FORM = True


Usage
=====
Just use it as any django-admin-action: Select your items, choose csvexport
from the admin-action-bar and go. You will be led to a formular that allows
you to render your items as csv-data.
