# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

import mongoengine

from django.core import exceptions

from tastypie_mongoengine.resources import MongoEngineResource

from tastypie.resources import ALL
from tastypie.authorization import Authorization

from upaas_admin.apps.applications.models import Application
from upaas_admin.apiauth import UpaasApiKeyAuthentication


log = logging.getLogger(__name__)


class ApplicationResource(MongoEngineResource):

    class Meta:
        queryset = Application.objects.all()
        resource_name = 'application'
        excludes = ['owner']
        filtering = {
            'id': ALL,
            'name': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def obj_create(self, bundle, request=None, **kwargs):
        log.debug(u"Going to create new application for user "
                  u"'%s'" % bundle.request.user.username)
        if Application.objects(owner=bundle.request.user,
                               name=bundle.data['name']):
            log.warning(u"Can't create new application, duplicated name '%s' "
                        u"for user '%s'" % (bundle.data['name'],
                                            bundle.request.user.username))
            raise exceptions.ValidationError(
                u"User '%s' already created application with name '%s'" % (
                    bundle.request.user.username, bundle.data['name']))
        try:
            ret = super(MongoEngineResource, self).obj_create(
                bundle, request=request, **kwargs)
        except mongoengine.ValidationError, e:
            log.warning(u"Can't create new application, invalid data payload: "
                        "%s" % e.message)
            raise exceptions.ValidationError(e.message)
        except mongoengine.NotUniqueError, e:
            log.warning(u"Can't create new application, duplicated fields: "
                        "%s" % e.message)
            raise exceptions.ValidationError(e.message)
        else:
            ret.obj.owner = [bundle.request.user]
            ret.obj.save()
            log.info(u"User %s created new application '%s' with id %s" % (
                bundle.request.user.username, bundle.obj.name, bundle.obj.id))
            return ret

    def apply_authorization_limits(self, request, object_list):
        log.debug(u"Limiting query to user owned apps "
                  u"(length: %d)" % len(object_list))
        return object_list.filter(owner=request.user)