# -*- coding: utf-8 -*-

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from django.db.utils import IntegrityError

from ...models import ModelA, ModelB, ModelC, ModelD


def create_test_data():
    try:
        User.objects.create_superuser(
            'admin',
            'admin@testapp.org',
            'adminpassword')
    except IntegrityError:
        pass
    try:
        user = User.objects.create_user(
            'anyuser',
            'anyuser@testapp.org',
            'anyuserpassword',
            is_staff=True)
    except IntegrityError:
        pass
    else:
        perms = ['view_modela', 'view_modelb', 'view_modeld']
        for name in perms:
            perm = Permission.objects.get(codename=name)
            user.user_permissions.add(perm)

    for i in range(5):
        ma = ModelA()
        mb = ModelB()
        mc = ModelC()
        mc2 = ModelC()
        md = ModelD()
        ma.duration_field = timedelta(hours=i)
        mb.duration_field = timedelta(hours=i)
        mc.duration_field = timedelta(hours=i)
        mc2.duration_field = timedelta(hours=i)
        md.duration_field = timedelta(hours=i)
        md.save()
        mc.model_d = md
        mc.save()
        mc2.model_d = md
        mc2.save()
        mb.model_c = mc2
        mb.save()
        ma.model_b = mb
        ma.model_c = mc
        ma.save()
    mb.model_c = None
    mb.save()


class Command(BaseCommand):
    help = 'Administrative actions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--create-test-data',
            action='store_true',
            help='Create testdata.')

    def handle(self, *args, **options):
        if options['create_test_data']:
            create_test_data()
