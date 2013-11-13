# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config.metadata import MetadataConfig

from django import forms
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from upaas_admin.common.forms import (CrispyForm, CrispyMongoForm,
                                      InlineCrispyMongoForm)
from upaas_admin.apps.applications.models import Application


class _MetadataForm(object):

    def clean_metadata(self):
        metadata = self.cleaned_data['metadata']
        try:
            meta = metadata.read()
            MetadataConfig.from_string(meta)
            metadata = meta
        except:
            raise forms.ValidationError(_(u"Invalid metadata file"))
        return metadata


class RegisterApplicationForm(CrispyMongoForm, _MetadataForm):

    submit_label = 'Register'
    form_action = reverse_lazy('app_register')
    layout = ['name', 'metadata']

    class Meta:
        document = Application
        fields = ('name',)

    metadata = forms.FileField()


class UpdateApplicationMetadataForm(CrispyMongoForm, _MetadataForm):

    submit_label = 'Update'
    layout = ['metadata']

    class Meta:
        document = Application
        fields = ('metadata',)

    metadata = forms.FileField()


class UpdateApplicationMetadataInlineForm(InlineCrispyMongoForm,
                                          _MetadataForm):

    submit_label = 'Update'

    class Meta:
        document = Application
        fields = ('metadata',)

    metadata = forms.FileField()


class BuildPackageForm(CrispyForm):

    submit_label = 'Build'
    layout = ['force_fresh']

    force_fresh = forms.BooleanField(required=False)


class StopApplicationForm(CrispyForm):

    submit_label = 'Stop'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)


class RollbackApplicationForm(CrispyForm):

    submit_label = 'Rollback'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)


class ApplicatiomMetadataFromPackageForm(CrispyForm):

    submit_label = 'Save'
    layout = ['confirm']

    confirm = forms.BooleanField(required=True)
