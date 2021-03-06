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


@admin.register(ModelC)
class ModelCAdmin(admin.ModelAdmin):
    actions = [csvexport]


@admin.register(ModelD)
class ModelDAdmin(admin.ModelAdmin):
    actions = [csvexport]
