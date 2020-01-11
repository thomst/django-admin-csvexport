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
from .forms import ExportAsCSV


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
    def __init__(self):
        self.data = str()

    def write(self, data):
        self.data += data


def get_fields(model):
    fields = model._meta.get_fields()
    fields = [f for f in fields if any(issubclass(type(f), F) for F in SUPPORTED_FIELDS)]
    return fields


def get_rel_fields(model):
    fields = model._meta.get_fields()
    fields = [f for f in fields if issubclass(type(f), ForeignKey)]
    return fields


def get_choices(model, ref=None):
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
        widget=forms.CheckboxSelectMultiple,
        choices=get_choices(model, ref),
        required=False)


def get_value(item, choice):
    fields = choice.split('.')
    for field in fields:
        value = getattr(item, field)
        item = value
    return str(value)


def export_as_csv(modeladmin, request, queryset):

    if 'export_as_csv' in request.POST:
        form = ExportAsCSV(request.POST)
    else:
        form = ExportAsCSV()

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
        csv_format['delimiter'] = request.POST.get('delimiter') or ','
        csv_format['escapechar'] = request.POST.get('escapechar') or '\\'
        csv_format['quotechar'] = request.POST.get('quotechar') or ''
        csv_format['doublequote'] = request.POST.get('doublequote') or ''
        newline = request.POST.get('lineterminator') or '\r\n'
        csv_format['lineterminator'] = codecs.decode(newline, 'unicode_escape')
        csv_format['quoting'] = csv.QUOTE_ALL if csv_format['quotechar'] else csv.QUOTE_NONE

        csv_data = CSVData()
        writer = csv.writer(csv_data, **csv_format)
        header = list()
        for form_field in form_fields.keys():
            header += list(form.cleaned_data[form_field])

        writer.writerow(tuple(f for f in header))
        for item in queryset:
            writer.writerow(tuple(get_value(item, f) for f in header))

        return HttpResponse(csv_data.data, content_type="text/plain")

    else:
        return render(request, 'admin/export_as_csv.html', {
            'objects': queryset.order_by('pk'),
            'form': form,
            'title': _('CSV-Export')
            })
