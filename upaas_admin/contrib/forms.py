# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoforms import MongoForm
from mongoforms.fields import MongoFormFieldGenerator

from IPy import IP

from django.forms import GenericIPAddressField, ValidationError
from django.utils.translation import ugettext_lazy as _
from django.forms.fields import validators

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.bootstrap import StrictButton


class IPField(GenericIPAddressField):

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        try:
            return IP(value)
        except ValueError, e:
            raise ValidationError(e)


class ContribFormFieldGenerator(MongoFormFieldGenerator):

    def generate_ipv4field(self, field_name, field, label):
        return IPField(label=label, required=field.required,
                       initial=field.default)


class CrispyForm(MongoForm):

    submit_label = 'Submit'
    form_action = None
    form_class = 'form-horizontal'
    label_class = 'col-md-2'
    field_class = 'col-md-8'
    layout = []

    def __init__(self, *args, **kwargs):
        super(CrispyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = self.form_action
        self.helper.form_class = self.form_class
        self.helper.label_class = self.label_class
        self.helper.field_class = self.field_class
        layout = self.layout + [
            StrictButton(_("Cancel"), css_class='btn-default',
                         onclick='javascript:history.go(-1);'),
            StrictButton(_(self.submit_label), css_class='btn-primary',
                         type='submit'),
        ]
        self.helper.layout = Layout(*layout)


class InlineCrispyForm(MongoForm):

    submit_label = 'Submit'
    form_action = None
    form_class = 'form-inline'
    label_class = 'col-md-3'
    field_class = 'col-md-7'
    layout = []

    def __init__(self, *args, **kwargs):
        super(InlineCrispyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = self.form_action
        self.helper.form_class = self.form_class
        self.helper.label_class = self.label_class
        self.helper.field_class = self.field_class
        self.helper.field_template = 'bootstrap3/layout/inline_field.html'
        layout = self.layout + [
            StrictButton(_(self.submit_label), css_class='btn-primary',
                         type='submit'),
        ]
        self.helper.layout = Layout(*layout)
