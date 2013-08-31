# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config.metadata import MetadataConfig

from django import forms

from mongoforms import MongoForm

from upaas_admin.apps.applications.models import Application


class RegisterApplicationForm(MongoForm):

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
            raise forms.ValidationError(u"Invalid metadata file")
        return metadata
