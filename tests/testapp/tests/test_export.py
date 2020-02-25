

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

        self.post_data['ModelA'] = list()
        for field in get_fields(ModelA):
            self.post_data['ModelA'].append(field.name)
        for rel_field in get_rel_fields(ModelA):
            model = rel_field.related_model
            fields = get_fields(model)
            self.post_data[model.__name__] = list()
            for field in get_fields(model):
                ref = '{}.{}'.format(rel_field.name, field.name)
                self.post_data[model.__name__].append(ref)

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
        post_data = self.post_data.copy()
        post_data['csvexport_view'] = 'View'
        del post_data['ModelA']
        del post_data['ModelB']
        del post_data['ModelC']

        # test without any selected field...
        resp = self.client.post(self.url, post_data)
        # self.assertEqual(resp.redirect_chain[0][0], url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(CSVFieldsForm.ERR_MSG, resp.content.decode('utf-8'))

    def test_03_csv_view(self):
        post_data = self.post_data.copy()
        post_data['csvexport_view'] = 'View'
        resp = self.client.post(self.url, post_data)
        self.assertEqual(resp.status_code, 200)

        # test default-values
        self.assertIn(BYTE_STRING, resp.content)
        self.assertIn(UNICODE_STRING, resp.content.decode('utf-8'))

        # test header
        header_a = ','.join(post_data['ModelA'])
        self.assertIn(header_a, resp.content.decode('utf-8'))
        header_b = ','.join(post_data['ModelB'])
        self.assertIn(header_b, resp.content.decode('utf-8'))
        header_c = ','.join(post_data['ModelC'])
        self.assertIn(header_c, resp.content.decode('utf-8'))

    def test_04_csv_download(self):
        # FIXME: Don't get a download-response or don't know how to test it...
        post_data = self.post_data.copy()
        post_data['csvexport_download'] = 'Download'
        resp = self.client.post(self.url, post_data)
        self.assertEqual(resp.status_code, 200)
