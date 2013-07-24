# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import forms

from mongoforms import MongoForm

from mongoengine.django.auth import make_password

from upaas_admin.apps.users.models import User


class AdminEditUserForm(MongoForm):

    class Meta:
        document = User
        exclude = ('username', 'password', 'is_staff', 'last_login',
                   'date_joined', 'apikey')


class AdminCreateUserForm(MongoForm):

    class Meta:
        document = User
        exclude = ('is_staff', 'last_login', 'date_joined', 'apikey')

    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_password(self):
        if self.cleaned_data['password']:
            return make_password(self.cleaned_data['password'])
        return None
