# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _


class CheckboxSelectAll(forms.CheckboxSelectMultiple):
    """
    Add a select-all-checkbox for the CheckboxSelectMultiple-widget.
    """
    template_name = 'csvexport/checkbox_select_all.html'

    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.js',
            'csvexport/checkbox_select_all.js')


class CSVFieldsForm(forms.Form):
    """
    A form holding the fields of models as multiple-choice-fields.
    Fields are added dynamically. At least one option of all fields must be
    checked.
    """
    ERR_MSG = "Model-fields must be selected in order to export them."

    def clean(self):
        """
        At least one option of one multiple-choice-field must be checked.
        """
        cleaned_data = super().clean()

        if not any(f for f in cleaned_data.values()):
            raise forms.ValidationError(self.ERR_MSG)

        return cleaned_data


class CSVFormatForm(forms.Form):
    delimiter = forms.CharField(
        label=_('Delimiter'),
        help_text=_("A one-character string used to separate fields."),
        widget=forms.TextInput(attrs={'placeholder': ',', 'maxlength': 1}),
        required=False
    )
    escapechar = forms.CharField(
        label=_('Escapechar'),
        help_text=_("A one-character string to escape the delimiter and "
                    "the quotechar if doublequote is False."),
        widget=forms.TextInput(attrs={'placeholder': '\\', 'maxlength': 1}),
        required=False
    )
    lineterminator = forms.CharField(
        label=_('Lineterminator'),
        help_text=_("The string used to terminate lines."),
        widget=forms.TextInput(attrs={'placeholder': r'\r\n'}),
        required=False
    )
    quotechar = forms.CharField(
        label=_('Quotechar'),
        help_text=_("A one-character string used to quote fields."),
        widget=forms.TextInput(attrs={'maxlength': 1}),
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
