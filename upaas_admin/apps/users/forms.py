# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm
from django.core.urlresolvers import reverse_lazy

from mongoforms import MongoForm

from upaas_admin.apps.users.models import User
from upaas_admin.common.forms import CrispyForm


class ResetApiKeyForm(forms.Form):
    apikey = forms.CharField(widget=forms.HiddenInput, required=True)

    def clean_apikey(self):
        if self._current_apikey != self.cleaned_data.get('apikey'):
            raise forms.ValidationError(
                _(u"Current API key verification failed"))


class SelfEditAccountForm(MongoForm):
    class Meta:
        document = User
        fields = ('first_name', 'last_name', 'email')


class UserPasswordChangeForm(CrispyForm, PasswordChangeForm):

    submit_label = 'Change'
    form_action = reverse_lazy('django.contrib.auth.views.password_change')
    layout = ['old_password', 'new_password1', 'new_password2']
    label_class = 'col-md-3'
    field_class = 'col-md-5'
