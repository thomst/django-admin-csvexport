

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from csvexport import apps, settings
from csvexport.actions import get_fields
from csvexport.actions import get_rel_fields
from csvexport.forms import CSVFieldsForm, CSVFormatForm
from ..models import ModelA, ModelB, ModelC, ModelD
from ..models import UNICODE_STRING
from ..models import BYTE_STRING
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
        field_names = [f.name for f in get_fields(ModelD)]
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

        self.admin = User.objects.get(username='admin')
        self.client.force_login(self.admin)
        self.url = reverse('admin:testapp_modela_changelist')

        self.post_data = dict()
        self.post_data['action'] = 'csvexport'
        self.post_data['csvexport'] = 'csvexport'
        self.post_data['_selected_action'] = [i for i in range(1,6)]

        self.csv_format = dict()
        self.csv_format['delimiter'] = settings.CSV_EXPORT_DELIMITER
        self.csv_format['escapechar'] = settings.CSV_EXPORT_ESCAPECHAR
        self.csv_format['lineterminator'] = settings.CSV_EXPORT_LINETERMINATOR
        self.csv_format['quotechar'] = settings.CSV_EXPORT_QUOTECHAR
        self.csv_format['doublequote'] = 'off'

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
        resp = self.client.post(self.url, post_data)

        # check form with format-form
        self.assertEqual(resp.status_code, 200)
        for field in format_form.fields.keys():
            self.assertIn(field, resp.content.decode('utf-8'))
        for option in self.options:
            self.assertIn(option, resp.content.decode('utf-8'))

        # check form without format-form
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url, post_data)
            self.assertEqual(resp.status_code, 200)
            for field in format_form.fields.keys():
                self.assertNotIn(field, resp.content.decode('utf-8'))

    def test_02_invalid_form(self):
        # test without any selected field...
        post_data = self.post_data.copy()
        post_data['csvexport_view'] = 'View'
        resp = self.client.post(self.url, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(CSVFieldsForm.ERR_MSG, resp.content.decode('utf-8'))

    def test_03_csv_view(self):
        post_data = self.post_data.copy()
        post_data.update(self.fields)
        post_data['csvexport_view'] = 'View'

        # without csv-format-data
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url, post_data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/plain", resp.get('Content-Type'))
            self.check_content(resp.content, post_data)

        # with format-data
        post_data.update(self.csv_format)
        resp = self.client.post(self.url, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/plain", resp.get('Content-Type'))
        self.check_content(resp.content, post_data)

    def test_04_csv_download(self):
        post_data = self.post_data.copy()
        post_data.update(self.fields)
        post_data['csvexport_download'] = 'Download'

        # without csv-format-data
        with AlterSettings(CSV_EXPORT_FORMAT_FORM=False):
            resp = self.client.post(self.url, post_data)
            self.check_content(resp.content, post_data)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get('Content-Type'), "text/comma-separated-values")

        # with format-data
        post_data.update(self.csv_format)
        resp = self.client.post(self.url, post_data)
        self.check_content(resp.content, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Content-Type'), "text/comma-separated-values")
