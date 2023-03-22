# -*- coding: utf-8 -*-

from django.contrib import admin
from csvexport.actions import csvexport

from .models import ModelA
from .models import ModelB
from .models import ModelC
from .models import ModelD


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
    csvexport_reference_depth = 0


@admin.register(ModelD)
class ModelDAdmin(admin.ModelAdmin):
    actions = [csvexport]
