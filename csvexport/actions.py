# -*- coding: utf-8 -*-
import csv
import codecs
from anytree import LevelOrderIter
from modeltree import ModelTree
from django.db.models import Field
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from functools import cached_property

from csvexport import settings
from .forms import CSVFormatForm
from .forms import UniqueForm
from .forms import CSVFieldsForm
from .forms import CheckboxSelectAll


class BaseModelTree(ModelTree):
    """
    A node per model to map their relations and access their fields.
    """
    export_fields = list()
    selected_fields = list()

    FOLLOW_ACROSS_APPS = True

    RELATION_TYPES = [
        'one_to_one',
        'many_to_one',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = list()
        self.initial = list()
        self.build_choices()

    @classmethod
    def setup(cls, modeladmin, request):
        params = dict(
            request = request,
            export_fields=getattr(modeladmin, 'csvexport_export_fields', list()),
            selected_fields=getattr(modeladmin, 'csvexport_selected_fields', list()),
            MAX_DEPTH=getattr(modeladmin, 'csvexport_reference_depth', settings.CSV_EXPORT_REFERENCE_DEPTH),
        )
        return type('ExportModelTree', (cls,), params)

    @property
    def key(self):
        return '_'.join(f'{n.field.name if n.field else "root"}__{n.model.__name__}' for n in self.path)

    @property
    def user_has_view_permission(self):
        perm = f'{self.model._meta.app_label}.view_{self.model._meta.model_name}'
        return self.request.user.has_perm(perm)

    def build_choices(self):
        """
        Get choice-tuples for a given model, including cached_property fields.
        """
        path = '__'.join(f'{n.field.name if n.field else "root"}' for n in self.path[1:])
        fields = [f for f in self.model._meta.get_fields() if not f.is_relation]
        cached_properties = [attr for attr in dir(self.model) if isinstance(getattr(self.model, attr), cached_property)]

        for field in fields + cached_properties:
            if isinstance(field, str):
                choice = f'{path}__{field}' if path else field
            else:
                choice = f'{path}__{field.name}' if path else field.name

            if not self.export_fields or choice in self.export_fields:
                self.choices.append((choice, field.name if isinstance(field, Field) else field))
                if self.selected_fields and choice in self.selected_fields:
                    self.initial.append(choice)

    def get_form_field(self):
        if self.choices:
            label = ' -> '.join(f'{n.field.name if n.field else "root"} ({n.model._meta.verbose_name})' for n in self.path)
            help_text = _('Which fields do you want to export?')
            return forms.MultipleChoiceField(
                label=label,
                help_text=help_text,
                widget=CheckboxSelectAll,
                choices=self.choices,
                initial=self.initial,
                required=False)


class IterNodesWithChoicesAndPermission(LevelOrderIter):
    """
    Only iter over Nodes with choices and where the user has view permission.
    """
    def __next__(self):
        node = super().__next__()
        if node.choices and node.user_has_view_permission:
            return node
        else:
            return next(self)


class CSVData:
    """
    Simple replacement for the filelike-object passed to the csv-writer.
    """
    def __init__(self, unique=False):
        self.data = list()
        self.unique = unique

    def write(self, data):
        if not self.unique or data not in self.data:
            self.data.append(data)

    def __str__(self):
        return ''.join(self.data)


def csvexport(modeladmin, request, queryset):
    """
    Admin-action to export items as csv-formatted data.
    """
    # initiate the format-form
    if 'csvexport' in request.POST and settings.CSV_EXPORT_FORMAT_FORM:
        format_form = CSVFormatForm(request.POST)
    else:
        format_form = CSVFormatForm(dict(
            delimiter=settings.CSV_EXPORT_DELIMITER,
            escapechar=settings.CSV_EXPORT_ESCAPECHAR,
            quotechar=settings.CSV_EXPORT_QUOTECHAR,
            doublequote=settings.CSV_EXPORT_DOUBLEQUOTE,
            quoting=settings.CSV_EXPORT_QUOTING,
            lineterminator=settings.CSV_EXPORT_LINETERMINATOR,
        ))

    # initiate unique-form
    if 'csvexport' in request.POST and settings.CSV_EXPORT_UNIQUE_FORM:
        unique_form = UniqueForm(request.POST)
    else:
        unique_form = UniqueForm(dict(uniq=False))

    # initiate field-form
    if 'csvexport' in request.POST:
        fields_form = CSVFieldsForm(request.POST)
    else:
        fields_form = CSVFieldsForm()

    # Build up the node-tree
    tree_class = BaseModelTree.setup(modeladmin, request)
    root_node = tree_class(modeladmin.model)

    # Add form-fields to form
    for node in IterNodesWithChoicesAndPermission(root_node):
        field_key = node.key
        if field_key not in fields_form.fields:
            fields_form.fields[field_key] = node.get_form_field()

    # Write and return csv-data
    if 'csvexport' in request.POST and format_form.is_valid() and fields_form.is_valid() and (not unique_form or unique_form.is_valid()):
        # get csv-format
        csv_format = dict()
        csv_format['delimiter'] = format_form.cleaned_data['delimiter']
        csv_format['escapechar'] = format_form.cleaned_data['escapechar']
        csv_format['quotechar'] = format_form.cleaned_data['quotechar']
        csv_format['doublequote'] = format_form.cleaned_data['doublequote']
        csv_format['quoting'] = getattr(csv, format_form.cleaned_data['quoting'])
        newline = format_form.cleaned_data['lineterminator']
        csv_format['lineterminator'] = codecs.decode(newline, 'unicode_escape')

        # use select-options as csv-header
        header = list()
        for node in IterNodesWithChoicesAndPermission(root_node):
            field_key = node.key
            if field_key in fields_form.cleaned_data:
                header.extend(fields_form.cleaned_data[field_key])

        csv_data = CSVData(unique_form.cleaned_data['unique'] if unique_form else False)

        # write csv-header and -data and return csv-data as view or download
        try:
            writer = csv.writer(csv_data, **csv_format)
            writer.writerow(tuple(f for f in header))
            # iterate over the queryset directly instead of values_list to include cached properties
            for obj in queryset:
                row = []
                for field_path in header:
                    value = obj
                    for attr in field_path.split('__'):
                        value = getattr(value, attr, settings.CSV_EXPORT_EMPTY_VALUE)
                        if callable(value):
                            value = value()
                    row.append(value if value is not None and value != '' else settings.CSV_EXPORT_EMPTY_VALUE)
                writer.writerow(tuple(row))
        except (csv.Error, TypeError) as exc:
            messages.error(request, 'Could not write csv-file: {}'.format(exc))
        else:
            if 'csvexport_view' in request.POST:
                content_type = "text/plain;charset=utf-8"
                response = HttpResponse(csv_data, content_type=content_type)
            elif 'csvexport_download' in request.POST:
                content_type = "text/csv"
                response = HttpResponse(csv_data, content_type=content_type)
                filename = modeladmin.model._meta.label_lower + '.csv'
                content_disposition = 'attachment; filename="{}"'.format(filename)
                response['Content-Disposition'] = content_disposition
            return response

    # If forms are invalid or csv-data couldn't be written return to the form
    format_form = format_form if settings.CSV_EXPORT_FORMAT_FORM else None
    unique_form = unique_form if settings.CSV_EXPORT_UNIQUE_FORM else None

    context = modeladmin.admin_site.each_context(request)
    context.update({
        'objects': queryset.order_by('pk'),
        'format_form': format_form,
        'unique_form': unique_form,
        'fields_form': fields_form,
        'title': _('CSV-Export')
        })

    return render(request, 'csvexport/csvexport.html', context)
