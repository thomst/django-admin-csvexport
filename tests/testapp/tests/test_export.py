
import re
from unittest.mock import MagicMock
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

from csvexport import settings
from csvexport.forms import CSVFieldsForm
from csvexport.forms import CSVFormatForm
from csvexport.forms import UniqueForm
from csvexport.actions import model_tree_factory
from ..models import ModelA
from ..models import ModelD
from ..models import UNICODE_STRING
from ..models import BYTE_STRING
from ..admin import ModelBAdmin
from ..management.commands.testapp import create_test_data


class AlterSettings:
    def __init__(self, **kwargs):
        self.settings = kwargs
        self.origin = dict()

    def __enter__(self):
        for setting, value in self.settings.items():
            self.origin[setting] = getattr(settings, setting)
            setattr(settings, setting, value)

    def __exit__(self, type, value, traceback):
        for setting, value in self.origin.items():
            setattr(settings, setting, value)


class ExportTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def setUp(self):
        self.anyuser = User.objects.get(username='anyuser')
        self.admin = User.objects.get(username='admin')
        self.options = list()
        self.fields = dict()

        request = MagicMock(user=self.admin)
        modeladmin = MagicMock(spec=[])
        tree_class = model_tree_factory(modeladmin, request)
        tree = tree_class(ModelA)
        field_names = [f.name for f in ModelA._meta.get_fields() if not f.is_relation]
        for node in tree.iterate_nodes_with_choices_and_permission():
            self.fields[node.field_name] = list()
            path = node.field_name.replace('root', '').replace('model_a__', '').replace('__', '.')
            for field in field_names:
                option = '{}.{}'.format(path, field).lstrip('.')
                self.options.append(option)
                self.fields[node.field_name].append(option)

        self.client.force_login(self.admin)
        self.url_a = reverse('admin:testapp_modela_changelist')
        self.url_b = reverse('admin:testapp_modelb_changelist')
        self.url_c = reverse('admin:testapp_modelc_changelist')

        self.form_post_data = dict()
        self.form_post_data['action'] = 'csvexport'
        self.form_post_data['_selected_action'] = [i for i in range(1,6)]
        self.export_post_data = self.form_post_data.copy()
        self.export_post_data['csvexport'] = 'csvexport'

        self.csv_format = dict()
        self.csv_format['delimiter'] = settings.CSV_EXPORT_DELIMITER
        self.csv_format['escapechar'] = settings.CSV_EXPORT_ESCAPECHAR
        self.csv_format['lineterminator'] = settings.CSV_EXPORT_LINETERMINATOR
        self.csv_format['quotechar'] = settings.CSV_EXPORT_QUOTECHAR
        self.csv_format['doublequote'] = settings.CSV_EXPORT_DOUBLEQUOTE
        self.csv_format['quoting'] = settings.CSV_EXPORT_QUOTING

    def check_content(self, content, post_data):
        # test default-values
        self.assertIn(BYTE_STRING, content)
        self.assertIn(UNICODE_STRING, content.decode('utf8'))

        # check header
        for option in self.options:
            self.assertIn(option, content.decode('utf8'))

    def test_form(self):
        format_form = CSVFormatForm()
        unique_form = UniqueForm()
        resp = self.client.post(self.url_a, self.form_post_data)

        # check all model-relations
        for option in self.options:
            self.assertIn('value="{}"'.format(option), resp.content.decode('utf-8'))

        # check form with format-form
        self.assertEqual(resp.status_code, 200)
        for field in format_form.fields.keys():
            self.assertIn(field, resp.content.decode('utf-8'))

        # check form without format-form
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url_a, self.form_post_data)
            self.assertEqual(resp.status_code, 200)
            for field in format_form.fields.keys():
                self.assertNotIn(field, resp.content.decode('utf-8'))

        # check form with and without unique-form
        self.assertNotIn(list(unique_form.fields.keys())[0], resp.content.decode('utf-8'))
        with AlterSettings(CSV_EXPORT_UNIQUE_FORM=True):
            resp = self.client.post(self.url_a, self.form_post_data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(list(unique_form.fields.keys())[0], resp.content.decode('utf-8'))

        # check form with defined export_fields and selected_fields
        resp = self.client.post(self.url_b, self.form_post_data)
        self.assertEqual(resp.status_code, 200)
        for option in ModelBAdmin.csvexport_export_fields:
            self.assertIn(f'value="{option}"', resp.content.decode('utf-8'))
        for option in ModelBAdmin.csvexport_selected_fields:
            self.assertRegex(resp.content.decode('utf-8'), f'value="{option}"[^>]+checked')
        for option in set(self.options) - set(ModelBAdmin.csvexport_export_fields):
            self.assertNotIn(f'value="{option}"', resp.content.decode('utf-8'))
        # check form with altered csvexport_reference_depth setting
        resp = self.client.post(self.url_c, self.form_post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('ModelC', resp.content.decode('utf-8'))
        self.assertNotIn('ModelC_ModelD', resp.content.decode('utf-8'))

        # check form with altered CSV_EXPORT_REFERENCE_DEPTH setting
        with AlterSettings(CSV_EXPORT_REFERENCE_DEPTH=1):
            resp = self.client.post(self.url_a, self.form_post_data)
            self.assertEqual(resp.status_code, 200)
            for field_name in ['root', 'model_b', 'model_c']:
                self.assertIn(field_name, resp.content.decode('utf-8'))
            for field_name in ['model_b__model_d', 'model_b__model_c', 'model_b__model_c__model_d']:
                self.assertNotIn(field_name, resp.content.decode('utf-8'))

    def test_invalid_form(self):
        # test without any selected field...
        post_data = self.export_post_data.copy()
        post_data['csvexport_view'] = 'View'
        resp = self.client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(CSVFieldsForm.ERR_MSG, resp.content.decode('utf-8'))

    def test_csv_error(self):
        post_data = self.export_post_data.copy()
        post_data.update(self.fields)
        post_data.update(self.csv_format)
        post_data['csvexport_view'] = 'View'
        post_data['quotechar'] = ''
        post_data['escapechar'] = ''

        # Without quotechar and escapechar the data couldn't be processed by csv
        resp = self.client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Could not write csv-file', resp.content.decode('utf-8'))

    def test_csv_view(self):
        post_data = self.export_post_data.copy()
        post_data.update(self.fields)
        post_data['csvexport_view'] = 'View'

        # without csv-format-data
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/plain", resp.get('Content-Type'))
            self.check_content(resp.content, post_data)

        # with format-data
        post_data.update(self.csv_format)
        resp = self.client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/plain", resp.get('Content-Type'))
        self.check_content(resp.content, post_data)

    def test_csv_download(self):
        post_data = self.export_post_data.copy()
        post_data.update(self.fields)
        post_data['csvexport_download'] = 'Download'

        # without csv-format-data
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url_a, post_data)
            self.check_content(resp.content, post_data)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get('Content-Type'), "text/csv")

        # with format-data
        post_data.update(self.csv_format)
        resp = self.client.post(self.url_a, post_data)
        self.check_content(resp.content, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Content-Type'), "text/csv")

    def test_custom_fields(self):
        field_names = [f.name for f in ModelD._meta.get_fields() if not f.is_relation]
        self.assertIn('custom_field', field_names)

    def test_uniq_result(self):
        post_data = self.export_post_data.copy()
        post_data.update(self.csv_format)
        post_data['model_b'] = ['model_b.char_field']
        post_data['model_b__model_c'] = ['model_b.model_c.char_field']
        post_data['csvexport_view'] = 'View'
        post_data['unique'] = True

        with AlterSettings(CSV_EXPORT_UNIQUE_FORM=False):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(len(resp.content.splitlines()), 6)

        with AlterSettings(CSV_EXPORT_UNIQUE_FORM=True):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(len(resp.content.splitlines()), 3)

    def test_permissions(self):
        client = Client()
        client.force_login(self.anyuser)
        post_data = dict()
        post_data['action'] = 'csvexport'
        post_data['_selected_action'] = [i for i in range(1,6)]
        resp = client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)

        # check if only the allowed models are used.
        for option in self.options:
            if re.match(r'^(model_c|model_b.model_c)\.[^.]+$', option):
                self.assertNotIn('value="{}"'.format(option), resp.content.decode('utf-8'))
            else:
                self.assertIn('value="{}"'.format(option), resp.content.decode('utf-8'))
