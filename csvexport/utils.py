from modeltree import ModelTree
from django.utils.translation import gettext_lazy as _
from django import forms
from . import settings
from .forms import CheckboxSelectAll


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

    @property
    def field_name(self):
        return self.field_path or 'root'

    @property
    def field_label(self):
        return str(self)

    @property
    def user_has_view_permission(self):
        perm = f'{self.model._meta.app_label}.view_{self.model._meta.model_name}'
        return self.request.user.has_perm(perm)

    def build_choices(self):
        """
        Get choice-tuples for a given model.
        """
        path = '.'.join(n.field.name for n in self.path[1:])
        fields = [f for f in self.model._meta.get_fields() if not f.is_relation]
        for field in fields:
            choice = '{}.{}'.format(path, field.name).lstrip('.')
            if not self.export_fields or choice in self.export_fields:
                self.choices.append((choice, field.name))
                if self.selected_fields and choice in self.selected_fields:
                    self.initial.append(choice)

    def get_form_field(self):
        if self.choices:
            help_text = _('Which fields do you want to export?')
            return forms.MultipleChoiceField(
                label=self.field_label,
                help_text=help_text,
                widget=CheckboxSelectAll,
                choices=self.choices,
                initial=self.initial,
                required=False)

    def iterate_nodes_with_choices_and_permission(self):
        filter_func = lambda node: node.choices and node.user_has_view_permission
        return super().iterate(by_level=True, filter=filter_func)


def model_tree_factory(modeladmin, request):
    params = dict(
        request = request,
        export_fields=getattr(modeladmin, 'csvexport_export_fields', list()),
        selected_fields=getattr(modeladmin, 'csvexport_selected_fields', list()),
        MAX_DEPTH=getattr(modeladmin, 'csvexport_reference_depth', settings.CSV_EXPORT_REFERENCE_DEPTH),
    )
    return type('ExportModelTree', (BaseModelTree,), params)
