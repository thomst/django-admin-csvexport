# -*- coding: utf-8 -*-

import uuid, os
from datetime import timedelta
from django.db import models
from django.utils.translation import gettext_lazy as _


UNICODE_STRING = 'ℋ ℌ ℍ,ℎ;ℏ ℐ ℑ ℒ ℓ'
BYTE_STRING = b'abcde'


class CustomField(models.Field):
    def cast_db_type(self, connection):
        return 'char'

    def db_type(self, connection):
        return 'char'

    def get_internal_type(self):
        return "CustomField"

    def to_python(self, value):
        if isinstance(value, str) or value is None:
            return value
        return str(value)


class Base(models.Model):
    class Meta:
        abstract = True

    boolean_field = models.BooleanField(default=True)
    char_field = models.CharField(max_length=255, default=UNICODE_STRING)
    date_field = models.DateField(auto_now=True)
    duration_field = models.DurationField()
    float_field = models.FloatField(default=1.234)
    integer_field = models.IntegerField(default=1234)
    text_field = models.TextField(default=UNICODE_STRING + '"') #we add a quotechar to trigger csv-write-errors
    time_field = models.TimeField(auto_now=True)
    binary_field = models.BinaryField(max_length=255, default=BYTE_STRING)
    uuid_field = models.UUIDField(default=uuid.uuid4)
    generic_ip_address_field = models.GenericIPAddressField(default='1.2.3.4')
    file_path = models.FilePathField(
        path=os.path.dirname(os.path.realpath(__file__)),
        default=os.path.basename(os.path.realpath(__file__)))
    custom_field = CustomField(default=UNICODE_STRING)


class ModelD(Base):
    pass

    class Meta:
        verbose_name = _('ModelD')


class ModelC(Base):
    model_d = models.ForeignKey(ModelD, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('ModelC')


class ModelB(Base):
    model_c = models.ForeignKey(ModelC, on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = _('ModelB')


class ModelA(Base):
    model_b = models.OneToOneField(ModelB, on_delete=models.CASCADE)
    model_c = models.ForeignKey(ModelC, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('ModelA')
