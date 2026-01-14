# -*- coding: utf-8 -*-
import csv
import codecs
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from . import settings
from .forms import CSVFormatForm
from .forms import UniqueForm
from .forms import CSVFieldsForm
from .utils import CSVData
from .utils import model_tree_factory


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
    tree_class = model_tree_factory(modeladmin, request)
    model_tree = tree_class(modeladmin.model)

    # Add form-fields to form
    for node in model_tree.iterate_nodes_with_choices_and_permission():
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
        for node in model_tree.iterate_nodes_with_choices_and_permission():
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
