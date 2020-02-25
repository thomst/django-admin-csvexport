

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ..models import ModelA
from ..models import ModelB
from ..models import ModelC
from ..management.commands.testapp import create_test_data


class ViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def setUp(self):
        self.admin = User.objects.get(username='admin')
        self.client.force_login(self.admin)

    def test_01_export(self):
        url_pattern = 'admin:{}_{}_changelist'
        post_data = dict()
