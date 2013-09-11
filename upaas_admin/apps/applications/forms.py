# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas.config.metadata import MetadataConfig

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from mongoforms import MongoForm

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.bootstrap import StrictButton

from upaas_admin.apps.applications.models import Application


class RegisterApplicationForm(MongoForm):

    class Meta:
        document = Application
        fields = ('name',)

    metadata = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(RegisterApplicationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('app_register')
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-2'
        self.helper.field_class = 'col-md-8'
        self.helper.layout = Layout(
            'name',
            'metadata',
            StrictButton(_("Cancel"), css_class='btn-default',
                         onclick='javascript:history.go(-1);'),
            StrictButton(_("Register"), css_class='btn-primary',
                         type='submit'),
        )

    def clean_metadata(self):
        metadata = self.cleaned_data['metadata']
        try:
            cfg = MetadataConfig.from_string(metadata.read())
            metadata = cfg.dump_string()
        except:
            raise forms.ValidationError(u"Invalid metadata file")
        return metadata
