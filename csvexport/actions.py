# -*- coding: utf-8 -*-
import csv
import codecs
from anytree import AnyNode
from anytree import LevelOrderGroupIter
from anytree import LevelOrderIter
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models.manager import BaseManager
from django import forms
from django.db import models

from csvexport import settings
from .forms import CSVFormatForm
from .forms import UniqueForm
from .forms import CSVFieldsForm
from .forms import CheckboxSelectAll


RELATION_TYPES = (
    models.OneToOneField,
    models.OneToOneRel,
    models.ForeignKey,
    models.ManyToOneRel,
    models.ManyToManyField,
    models.ManyToManyRel
)
SUPPORTED_RELATION_TYPES = (
    models.ForeignKey,
    models.OneToOneField,
    models.OneToOneRel
)


class ModelNode(AnyNode):
    """
    A node per model to map their relations and access their fields.
    """
    export_fields = list()
    selected_fields = list()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = list()
        self.initial = list()
        self.build_choices()

    @classmethod
    def setup(cls, modeladmin):
        cls.export_fields = getattr(modeladmin, 'csvexport_export_fields', list())
        cls.selected_fields = getattr(modeladmin, 'csvexport_selected_fields', list())

    @property
    def key(self):
        return '_'.join(n.model.__name__ for n in self.path)

    def build_choices(self):
        """
        Get choice-tuples for a given model.
        """
        path = '.'.join(n.field.name for n in self.path[1:])
        fields = self.get_fields()
        for field in fields:
            choice = '{}.{}'.format(path, field.name).lstrip('.')
            if not self.export_fields or choice in self.export_fields:
                self.choices.append((choice, field.name))
                if self.selected_fields and choice in self.selected_fields:
                    self.initial.append(choice)

    def get_fields(self):
        """
        Get all model fields that are not relations.
        """
        fields = self.model._meta.get_fields()
        check_type = lambda f: all(not issubclass(type(f), r) for r in RELATION_TYPES)
        fields = [f for f in fields if check_type(f)]
        return fields

    def get_rel_fields(self):
        """
        Get model fields that are subclasses of ForeignKey.
        """
        fields = self.model._meta.get_fields()
        check_type = lambda f: any(issubclass(type(f), r) for r in SUPPORTED_RELATION_TYPES)
        fields = [f for f in fields if check_type(f)]
        return fields

    def get_form_field(self):
        if self.choices:
            label = ' -> '.join(str(n.model._meta.verbose_name) for n in self.path)
            help_text = _('Which fields do you want to export?')
            return forms.MultipleChoiceField(
                label=label,
                help_text=help_text,
                widget=CheckboxSelectAll,
                choices=self.choices,
                initial=self.initial,
                required=False)


class IterNodesWithChoices(LevelOrderIter):
    """
    Only iter over Nodes with choices.
    """
    def __next__(self):
        node = super().__next__()
        if node.choices:
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
    ModelNode.setup(modeladmin)
    root_node = ModelNode(model=modeladmin.model)

    n = 0
    while n < settings.CSV_EXPORT_REFERENCE_DEPTH:
        n += 1
        for node in tuple(LevelOrderGroupIter(root_node))[-1]:
            for field in node.get_rel_fields():
                try:
                    # Do we have a OneToOneField OneToOneRel cycle?
                    # Then we just continue.
                    assert field.remote_field == node.field
                except (AttributeError, AssertionError):
                    # Otherwise we build a new Node.
                    current_node = ModelNode(model=field.related_model, field=field, parent=node)
                else:
                    continue

    # Add form-fields to form
    for node in IterNodesWithChoices(root_node):
        fields_form.fields[node.key] = node.get_form_field()

    # Write and return csv-data
    if format_form.is_valid() and fields_form.is_valid() and unique_form.is_valid():
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
        for node in IterNodesWithChoices(root_node):
            header += list(fields_form.cleaned_data[node.key])

        csv_data = CSVData(unique_form.cleaned_data['unique'])
        header_fields = [f.replace('.', '__') for f in header]
        related_fields = ['__'.join(f.split('__')[:-1]) for f in header_fields if '__' in f]
        if related_fields:
            queryset = queryset.select_related(*related_fields)

        # write csv-header and -data and return csv-data as view or download
        try:
            writer = csv.writer(csv_data, **csv_format)
            writer.writerow(tuple(f for f in header))
            for item in queryset.values_list(*header_fields):
                row = tuple(f if f is not None and f != '' else settings.CSV_EXPORT_EMPTY_VALUE for f in item)
                writer.writerow(row)
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
