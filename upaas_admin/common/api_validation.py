# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from tastypie.validation import CleanedDataFormValidation

from mongoforms import MongoForm


class MongoCleanedDataFormValidation(CleanedDataFormValidation):

    def form_args(self, bundle):
        kwargs = {}
        data = bundle.data
        if data:
            kwargs['data'] = data
        if issubclass(self.form_class, MongoForm):
            kwargs['instance'] = bundle.obj
        return kwargs

    def is_valid(self, bundle, request=None):
        form = self.form_class(**self.form_args(bundle))
        #FIXME bit hackish
        form.user = bundle.request.user
        if form.is_valid():
            return {}
        return form.errors
