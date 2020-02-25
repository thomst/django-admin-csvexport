

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from csvexport.actions import get_fields
from csvexport.actions import get_rel_fields
from csvexport.forms import CSVFieldsForm
from ..models import ModelA
from ..models import ModelB
from ..models import ModelC
from ..models import UNICODE_STRING
from ..models import BYTE_STRING
from ..management.commands.testapp import create_test_data


class ExportTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def setUp(self):
        self.admin = User.objects.get(username='admin')
        self.client.force_login(self.admin)
        self.url = reverse('admin:testapp_modela_changelist')
        self.post_data = dict()
        self.post_data['action'] = 'csvexport'
        self.post_data['csvexport'] = 'csvexport'
        self.post_data['delimiter'] = ''
        self.post_data['escapechar'] = ''
        self.post_data['lineterminator'] = ''
        self.post_data['quotechar'] = ''
        self.post_data['doublequote'] = 'off'
        self.post_data['_selected_action'] = [i for i in range(1,6)]

    def select_fields(self, post_data):
        post_data['ModelA'] = list()
        for field in get_fields(ModelA):
            post_data['ModelA'].append(field.name)
        for rel_field in get_rel_fields(ModelA):
            model = rel_field.related_model
            fields = get_fields(model)
            post_data[model.__name__] = list()
            for field in get_fields(model):
                ref = '{}.{}'.format(rel_field.name, field.name)
                post_data[model.__name__].append(ref)

    def check_content(self, content, post_data):
        # test default-values
        self.assertIn(BYTE_STRING, content)
        self.assertIn(UNICODE_STRING, content.decode('utf-8'))

        # test header
        header_a = ','.join(post_data['ModelA'])
        self.assertIn(header_a, content.decode('utf-8'))
        header_b = ','.join(post_data['ModelB'])
        self.assertIn(header_b, content.decode('utf-8'))
        header_c = ','.join(post_data['ModelC'])
        self.assertIn(header_c, content.decode('utf-8'))

    def test_01_form(self):
        post_data = dict()
        post_data['action'] = 'csvexport'
        post_data['_selected_action'] = [i for i in range(1,6)]
        resp = self.client.post(self.url, post_data)

        self.assertEqual(resp.status_code, 200)

        # test model-a-fields
        for field in get_fields(ModelA):
            self.assertIn(field.name, resp.content.decode('utf-8'))

        # test related-model-fields
        for rel_field in get_rel_fields(ModelA):
            model = rel_field.related_model
            fields = get_fields(model)
            for field in get_fields(model):
                ref = '{}.{}'.format(rel_field.name, field.name)
                self.assertIn(ref, resp.content.decode('utf-8'))

    def test_02_invalid_form(self):
        # test without any selected field...
        post_data = self.post_data.copy()
        post_data['csvexport_view'] = 'View'
        resp = self.client.post(self.url, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(CSVFieldsForm.ERR_MSG, resp.content.decode('utf-8'))

    def test_03_csv_view(self):
        post_data = self.post_data.copy()
        post_data['csvexport_view'] = 'View'
        self.select_fields(post_data)
        resp = self.client.post(self.url, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/plain", resp.get('Content-Type'))
        self.check_content(resp.content, post_data)

    def test_04_csv_download(self):
        post_data = self.post_data.copy()
        post_data['csvexport_download'] = 'Download'
        self.select_fields(post_data)
        resp = self.client.post(self.url, post_data)
        self.check_content(resp.content, post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Content-Type'), "text/comma-separated-values")
