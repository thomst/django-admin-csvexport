=================================
Welcome to django-admin-csvexport
=================================

.. image:: https://github.com/thomst/django-admin-csvexport/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/thomst/django-admin-csvexport/actions/workflows/ci.yml
   :alt: Run tests for django-admin-csvexport

.. image:: https://coveralls.io/repos/github/thomst/django-admin-csvexport/badge.svg?branch=master
   :target: https://coveralls.io/github/thomst/django-admin-csvexport?branch=master
   :alt: coveralls badge

.. image:: https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue
   :target: https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue
   :alt: python: 3.6, 3.7, 3.8, 3.9,3.9,3.10

.. image:: https://img.shields.io/badge/django-2.2%20%7C%203.0%20%7C%203.1%20%7C%203.2%20%7C%204.0%20%7C%204.1-orange
   :target: https://img.shields.io/badge/django-2.2%20%7C%203.0%20%7C%203.1%20%7C%203.2%20%7C%204.0%20%7C%204.1-orange
   :alt: django: 2.2, 3.0, 3.1, 3.2, 4.0, 4.1


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

The following settings define the csv-format to be used. The default values meet
the unix standard csv-format::

    CSV_EXPORT_DELIMITER = ','
    CSV_EXPORT_ESCAPECHAR = ''
    CSV_EXPORT_QUOTECHAR = '"'
    CSV_EXPORT_DOUBLEQUOTE = True
    CSV_EXPORT_LINETERMINATOR = r'\n'
    CSV_EXPORT_QUOTING = 'QUOTE_ALL'

For the newline escape sequence use a raw-string.

For :code:`CSV_EXPORT_QUOTING` use the name of one of these csv_ module
constants:

* QUOTE_ALL_
* QUOTE_MINIMAL_
* QUOTE_NONNUMERIC_
* QUOTE_NONE_

.. _csv: https://docs.python.org/3/library/csv.html
.. _QUOTE_ALL: https://docs.python.org/3/library/csv.html#csv.QUOTE_ALL
.. _QUOTE_MINIMAL: https://docs.python.org/3/library/csv.html#csv.QUOTE_ALL
.. _QUOTE_NONNUMERIC: https://docs.python.org/3/library/csv.html#csv.QUOTE_ALL
.. _QUOTE_NONE: https://docs.python.org/3/library/csv.html#csv.QUOTE_ALL

The csv-format can also be adjusted by the formular rendered by the csvexport
admin-action. If there is no need to adjust the csv-format on each export use::

    CSV_EXPORT_FORMAT_FORM = False

The formular can also be extended by a checkbox which allows to filter the
resulting csv rows to be unique. Therefore use::

    CSV_EXPORT_UNIQUE_FORM = True

With the following additional parameters for your ModelAdmin you could limit the
fields offered by the export form and choose them to be preselected::

    class MyModelAdmin(admin.ModelAdmin):
        csvexport_export_fields = [
            'field_a',
            'field_b,
            'relational_field.field_a_on_related_model',
            ...
        ]
        csvexport_selected_fields = [
            'field_a',
            'field_b,
            'relational_field.field_a_on_related_model',
            ...
        ]

Fields of related models could be referenced by using a dot between the
relational fields and the fields to be exported:
:code:`'relation_a.relation_b.any_field'`. Not defining
:code:`csvexport_export_fields` means all possible fields will be regarded.


Usage
=====
Just use it as any django-admin-action: Select your items, choose csvexport
from the admin-action-bar and go. You will be led to a formular that allows
you to view or download your items as csv-data.
