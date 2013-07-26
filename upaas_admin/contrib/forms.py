# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoforms.fields import MongoFormFieldGenerator

from IPy import IP

from django.forms import GenericIPAddressField, ValidationError
from django.forms.fields import validators


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
