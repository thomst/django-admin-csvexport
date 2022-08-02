# -*- coding: utf-8 -*-

from django.contrib import admin
from csvexport.actions import csvexport

from .models import ModelA
from .models import ModelB
from .models import ModelC
from .models import ModelD
from .models import Issue6Model


@admin.register(ModelA)
class ModelAAdmin(admin.ModelAdmin):
    actions = [csvexport]


@admin.register(ModelB)
class ModelBAdmin(admin.ModelAdmin):
    actions = [csvexport]
    csvexport_export_fields = [
        'boolean_field',
        'char_field',
        'date_field',
        'model_c.boolean_field',
        'model_c.char_field',
        'model_c.date_field',
        'model_c.model_d.boolean_field',
        'model_c.model_d.char_field',
        'model_c.model_d.date_field',
    ]
    csvexport_selected_fields = [
        'boolean_field',
        'model_c.boolean_field',
        'model_c.model_d.boolean_field',
    ]


@admin.register(ModelC)
class ModelCAdmin(admin.ModelAdmin):
    actions = [csvexport]


@admin.register(ModelD)
class ModelDAdmin(admin.ModelAdmin):
    actions = [csvexport]


@admin.register(Issue6Model)
class Issue6ModelAdmin(admin.ModelAdmin):
    actions = [csvexport]
    csvexport_export_fields = [
        'id',
        'model_a.integer_field',
        'model_b.integer_field',
    ]
    csvexport_selected_fields = [
        'id',
        'model_a.integer_field',
        'model_b.integer_field',
    ]
