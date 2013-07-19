# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import forms
from django.utils.translation import ugettext_lazy as _


class ResetApiKeyForm(forms.Form):
    apikey = forms.CharField(widget=forms.HiddenInput, required=True)

    def clean_apikey(self):
        if self._current_apikey != self.cleaned_data.get('apikey'):
            raise forms.ValidationError(
                _(u"Current API key verification failed"))
