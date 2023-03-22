
import re
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

from csvexport import apps, settings
from csvexport.forms import CSVFieldsForm
from csvexport.forms import CSVFormatForm
from csvexport.forms import UniqueForm
from ..models import ModelA, ModelB, ModelC, ModelD
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
        field_names = [f.name for f in ModelD._meta.get_fields() if not f.is_relation]
        paths = [
            ('', 'ModelA'),
            ('model_b.', 'ModelA_ModelB'),
            ('model_b.model_c.', 'ModelA_ModelB_ModelC'),
            ('model_b.model_c.model_d.', 'ModelA_ModelB_ModelC_ModelD'),
            ('model_c.', 'ModelA_ModelC'),
            ('model_c.model_d.', 'ModelA_ModelC_ModelD'),
        ]
        self.options = list()
        self.fields = dict()
        for path, name in paths:
            self.fields[name] = list()
            for field in field_names:
                option = '{}{}'.format(path, field)
                self.options.append(option)
                self.fields[name].append(option)

        self.anyuser = User.objects.get(username='anyuser')
        self.admin = User.objects.get(username='admin')
        self.client.force_login(self.admin)
        self.url_a = reverse('admin:testapp_modela_changelist')
        self.url_b = reverse('admin:testapp_modelb_changelist')
        self.url_c = reverse('admin:testapp_modelc_changelist')

        self.post_data = dict()
        self.post_data['action'] = 'csvexport'
        self.post_data['csvexport'] = 'csvexport'
        self.post_data['_selected_action'] = [i for i in range(1,6)]

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

    def test_01_form(self):
        post_data = dict()
        post_data['action'] = 'csvexport'
        post_data['_selected_action'] = [i for i in range(1,6)]
        format_form = CSVFormatForm()
        unique_form = UniqueForm()
        resp = self.client.post(self.url_a, post_data)

        # check all model-relations
        for option in self.options:
            self.assertIn('value="{}"'.format(option), resp.content.decode('utf-8'))

        # check if OneToOneField-OneToOneRel-cycle are prevented
        cycle_path = 'ModelA_ModelB_ModelA'
        self.assertNotIn(cycle_path, resp.content.decode('utf-8'))

        # check form with format-form
        self.assertEqual(resp.status_code, 200)
        for field in format_form.fields.keys():
            self.assertIn(field, resp.content.decode('utf-8'))

        # check form without format-form
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(resp.status_code, 200)
            for field in format_form.fields.keys():
                self.assertNotIn(field, resp.content.decode('utf-8'))

        # check form with and without unique-form
        self.assertNotIn(list(unique_form.fields.keys())[0], resp.content.decode('utf-8'))
        with AlterSettings(CSV_EXPORT_UNIQUE_FORM=True):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(list(unique_form.fields.keys())[0], resp.content.decode('utf-8'))

        # check form with defined export_fields and selected_fields
        resp = self.client.post(self.url_b, post_data)
        self.assertEqual(resp.status_code, 200)
        for option in ModelBAdmin.csvexport_export_fields:
            self.assertIn('value="{}"'.format(option), resp.content.decode('utf-8'))
        for option in ModelBAdmin.csvexport_selected_fields:
            self.assertRegex(resp.content.decode('utf-8'), r'value="{}".+checked'.format(option))
        for option in set(self.options) - set(ModelBAdmin.csvexport_export_fields):
            self.assertNotIn('value="{}"'.format(option), resp.content.decode('utf-8'))

        # check form with altered csvexport_reference_depth setting
        resp = self.client.post(self.url_c, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('ModelC', resp.content.decode('utf-8'))
        self.assertNotIn('ModelC_ModelD', resp.content.decode('utf-8'))

        # check form with altered CSV_EXPORT_REFERENCE_DEPTH setting
        with AlterSettings(CSV_EXPORT_REFERENCE_DEPTH=1):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(resp.status_code, 200)
            for field_name in ['ModelA', 'ModelA_ModelB', 'ModelA_ModelC']:
                self.assertIn(field_name, resp.content.decode('utf-8'))
            for field_name in ['ModelA_ModelB_ModelD', 'ModelA_ModelB_ModelC', 'ModelA_ModelB_ModelC_ModelD']:
                self.assertNotIn(field_name, resp.content.decode('utf-8'))



    def test_02_invalid_form(self):
        # test without any selected field...
        post_data = self.post_data.copy()
        post_data['csvexport_view'] = 'View'
        resp = self.client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(CSVFieldsForm.ERR_MSG, resp.content.decode('utf-8'))

    def test_03_csv_error(self):
        post_data = self.post_data.copy()
        post_data.update(self.fields)
        post_data.update(self.csv_format)
        post_data['csvexport_view'] = 'View'
        post_data['quotechar'] = ''
        post_data['escapechar'] = ''

        # Without quotechar and escapechar the data couldn't be processed by csv
        resp = self.client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Could not write csv-file', resp.content.decode('utf-8'))

    def test_04_csv_view(self):
        post_data = self.post_data.copy()
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

    def test_05_csv_download(self):
        post_data = self.post_data.copy()
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

    def test_06_custom_fields(self):
        field_names = [f.name for f in ModelD._meta.get_fields() if not f.is_relation]
        self.assertIn('custom_field', field_names)

    def test_07_uniq_result(self):
        post_data = self.post_data.copy()
        post_data.update(self.csv_format)
        fields = dict(
            ModelA_ModelB=['model_b.boolean_field'],
            ModelA_ModelB_ModelC=['model_b.model_c.char_field']
        )
        post_data.update(fields)
        post_data['csvexport_view'] = 'View'
        post_data['unique'] = True

        with AlterSettings(CSV_EXPORT_UNIQUE_FORM=False):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(len(resp.content.splitlines()), 6)

        with AlterSettings(CSV_EXPORT_UNIQUE_FORM=True):
            resp = self.client.post(self.url_a, post_data)
            self.assertEqual(len(resp.content.splitlines()), 3)

    def test_08_permissions(self):
        client = Client()
        client.force_login(self.anyuser)
        post_data = dict()
        post_data['action'] = 'csvexport'
        post_data['_selected_action'] = [i for i in range(1,6)]
        resp = client.post(self.url_a, post_data)
        self.assertEqual(resp.status_code, 200)

        # check if only the allowed models are used.
        for option in self.options:
            if re.match('^(model_c|model_b.model_c)\.[^.]+$', option):
                self.assertNotIn('value="{}"'.format(option), resp.content.decode('utf-8'))
            else:
                self.assertIn('value="{}"'.format(option), resp.content.decode('utf-8'))
