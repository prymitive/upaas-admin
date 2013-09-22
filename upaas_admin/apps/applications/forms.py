# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config.metadata import MetadataConfig

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from upaas_admin.contrib.forms import CrispyForm
from upaas_admin.apps.applications.models import Application


class RegisterApplicationForm(CrispyForm):

    submit_label = 'Register'
    form_action = reverse_lazy('app_register')
    layout = ['name', 'metadata']

    class Meta:
        document = Application
        fields = ('name',)

    metadata = forms.FileField()

    def clean_metadata(self):
        metadata = self.cleaned_data['metadata']
        try:
            cfg = MetadataConfig.from_string(metadata.read())
            metadata = cfg.dump_string()
        except:
            raise forms.ValidationError(_(u"Invalid metadata file"))
        return metadata
