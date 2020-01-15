# -*- coding: utf-8 -*-
import csv
import codecs
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models.manager import BaseManager
from django import forms
from django.db.models import ForeignKey
from django.db.models.fields import AutoField
from django.db.models.fields import BooleanField
from django.db.models.fields import CharField
from django.db.models.fields import DateField
from django.db.models.fields import DurationField
from django.db.models.fields import FilePathField
from django.db.models.fields import FloatField
from django.db.models.fields import IntegerField
from django.db.models.fields import IPAddressField
from django.db.models.fields import TextField
from django.db.models.fields import TimeField
from django.db.models.fields import BinaryField
from django.db.models.fields import UUIDField
from django.db.models.fields import GenericIPAddressField
from .forms import CSVExportForm
from .forms import CheckboxSelectAll


SUPPORTED_FIELDS = (
    AutoField,
    BooleanField,
    CharField,
    DateField,
    DurationField,
    FilePathField,
    FloatField,
    IntegerField,
    IPAddressField,
    TextField,
    TimeField,
    BinaryField,
    UUIDField,
    GenericIPAddressField
)

class CSVData:
    """
    Simple replacement for the filelike-object passed to the csv-writer.
    """
    DELIMITER = ','
    ESCAPECHAR = '\\'
    QUOTECHAR = ''
    LINETERMINATOR = '\r\n'
    DOUBLEQUOTE = False

    def __init__(self):
        self.data = str()

    def write(self, data):
        self.data += data

    def __str__(self):
        return self.data


def get_fields(model):
    """
    Get all model fields that are subclasses of SUPPORTED_FIELDS.
    """
    fields = model._meta.get_fields()
    fields = [f for f in fields if any(issubclass(type(f), F) for F in SUPPORTED_FIELDS)]
    return fields


def get_rel_fields(model):
    """
    Get model fields that are subclasses of ForeignKey.
    """
    fields = model._meta.get_fields()
    fields = [f for f in fields if issubclass(type(f), ForeignKey)]
    return fields


def get_choices(model, ref=None):
    """
    Get choice-tuples for a given model.
    """
    fields = get_fields(model)
    for field in fields:
        if ref:
            yield ('{}.{}'.format(ref.name, field.name), field.name)
        else:
            yield (field.name, field.name)


def get_form_field(model, ref=None):
    if ref:
        label = _('{} (related)'.format(model._meta.verbose_name))
    else:
        label = model._meta.verbose_name
    help_text = _('Which fields do you want to export?')
    return forms.MultipleChoiceField(
        label=label,
        help_text=help_text,
        widget=CheckboxSelectAll,
        choices=get_choices(model, ref),
        required=False)


def get_value(item, choice):
    fields = choice.split('.')
    for field in fields:
        value = getattr(item, field)
        item = value
    return str(value)


def csvexport(modeladmin, request, queryset):
    """
    Admin-action to export items as csv-formatted data.
    """
    if 'csvexport' in request.POST:
        form = CSVExportForm(request.POST)
    else:
        form = CSVExportForm()

    form_fields = dict()
    model = modeladmin.model
    form_fields[model.__name__] = get_form_field(model)
    rel_fields = get_rel_fields(model)
    for field in rel_fields:
        model = field.related_model
        form_fields[model.__name__] =  get_form_field(model, field)

    for key, form_field in form_fields.items():
        form.fields[key] = form_field

    if form.is_valid():
        # get csv-format
        csv_format = dict()
        csv_format['delimiter'] = request.POST.get('delimiter') or CSVData.DELIMITER
        csv_format['escapechar'] = request.POST.get('escapechar') or CSVData.ESCAPECHAR
        csv_format['quotechar'] = request.POST.get('quotechar') or CSVData.QUOTECHAR
        csv_format['doublequote'] = request.POST.get('doublequote') or CSVData.DOUBLEQUOTE
        newline = request.POST.get('lineterminator') or CSVData.LINETERMINATOR
        csv_format['lineterminator'] = codecs.decode(newline, 'unicode_escape')
        csv_format['quoting'] = csv.QUOTE_ALL if csv_format['quotechar'] else csv.QUOTE_NONE

        csv_data = CSVData()
        if 'csvexport_view' in request.POST:
            content_type="text/plain"
        elif 'csvexport_download' in request.POST:
            content_type="text/comma-separated-values"

        writer = csv.writer(csv_data, **csv_format)
        header = list()
        for form_field in form_fields.keys():
            header += list(form.cleaned_data[form_field])

        writer.writerow(tuple(f for f in header))
        for item in queryset:
            writer.writerow(tuple(get_value(item, f) for f in header))

        return HttpResponse(csv_data, content_type=content_type)

    else:
        return render(request, 'csvexport/csvexport.html', {
            'objects': queryset.order_by('pk'),
            'form': form,
            'title': _('CSV-Export')
            })
