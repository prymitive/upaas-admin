# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import forms

from mongoforms import MongoForm

from mongoengine.django.auth import make_password

from upaas_admin.common.forms import ContribFormFieldGenerator
from upaas_admin.apps.users.models import User
from upaas_admin.apps.servers.models import RouterServer, BackendServer


#FIXME patch crispy form-horizontal to support checkboxes and move to crispy
class AdminCreateUserForm(MongoForm):

    class Meta:
        document = User
        exclude = ('is_staff', 'last_login', 'date_joined', 'apikey')

    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_password(self):
        if self.cleaned_data['password']:
            return make_password(self.cleaned_data['password'])
        return None


class AdminEditUserForm(MongoForm):

    class Meta:
        document = User
        exclude = ('username', 'password', 'is_staff', 'last_login',
                   'date_joined', 'apikey')


class AdminRouterForm(MongoForm):

    class Meta:
        document = RouterServer
        exclude = ('date_created',)
        formfield_generator = ContribFormFieldGenerator


class AdminBackendForm(MongoForm):

    class Meta:
        document = BackendServer
        exclude = ('date_created', 'ports')
        formfield_generator = ContribFormFieldGenerator
