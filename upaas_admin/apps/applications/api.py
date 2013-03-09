# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import mongoengine

from django.core import exceptions

from tastypie_mongoengine.resources import MongoEngineResource

from tastypie.authorization import Authorization

from upaas_admin.apps.applications.models import Application
from upaas_admin.apiauth import UpaasApiKeyAuthentication


class ApplicationResource(MongoEngineResource):

    class Meta:
        queryset = Application.objects.all()
        resource_name = 'application'
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def obj_create(self, bundle, request=None, **kwargs):
        bundle.data['owners'] = bundle.request.user
        try:
            self._reset_collection()
            return super(MongoEngineResource, self).obj_create(
                bundle, request=request, **kwargs)
        except mongoengine.ValidationError, e:
            raise exceptions.ValidationError(e.message)

    def apply_authorization_limits(self, request, object_list):
        return object_list.filter(owner=request.user)
