# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.core.urlresolvers import reverse_lazy

from mongoforms import MongoForm

from passwords.fields import PasswordField

from upaas_admin.apps.users.models import User
from upaas_admin.common.forms import CrispyForm


class ResetApiKeyForm(CrispyForm):

    submit_label = 'Reset'
    form_action = reverse_lazy('users_apikey_reset')
    layout = ['apikey']

    apikey = forms.CharField(widget=forms.HiddenInput, required=True)

    def clean_apikey(self):
        if self._current_apikey != self.cleaned_data.get('apikey'):
            raise forms.ValidationError(
                _("Current API key verification failed"))


class SelfEditAccountForm(MongoForm):
    class Meta:
        document = User
        fields = ('first_name', 'last_name', 'email')


class UserPasswordChangeForm(CrispyForm, PasswordChangeForm):

    form_action = reverse_lazy('django.contrib.auth.views.password_change')
    layout = ['old_password', 'new_password1', 'new_password2']
    label_class = 'col-md-3'
    field_class = 'col-md-5'

    new_password2 = PasswordField(label=_("New password confirmation"))


class UserPasswordSetForm(SetPasswordForm):

    new_password2 = PasswordField(label=_("New password confirmation"))
