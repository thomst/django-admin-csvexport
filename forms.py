# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _


class ExportAsCSV(forms.Form):
    delimiter = forms.CharField(
        label=_('Delimiter'),
        help_text=_("A one-character string used to separate fields."),
        widget=forms.TextInput(attrs={'placeholder': ','}),
        required=False
    )
    escapechar = forms.CharField(
        label=_('Escapechar'),
        help_text=_("A one-character string used by the writer to escape the "
                    "delimiter and the quotechar if doublequote is False."),
        widget=forms.TextInput(attrs={'placeholder': '\\'}),
        required=False
    )
    lineterminator = forms.CharField(
        label=_('Lineterminator'),
        help_text=_("The string used to terminate lines produced by the writer."),
        widget=forms.TextInput(attrs={'placeholder': r'\r\n'}),
        required=False
    )
    quotechar = forms.CharField(
        label=_('Quotechar'),
        help_text=_("A one-character string used to quote fields."),
        required=False
    )
    doublequote = forms.BooleanField(
        label=_('Doublequote'),
        help_text=_("Controls how instances of quotechar appearing inside a "
                    "field should themselves be quoted. When True, the "
                    "character is doubled. When False, the escapechar "
                    "is used as a prefix to the quotechar."),
        required=False
    )
