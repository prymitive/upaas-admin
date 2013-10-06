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
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apiauth import UpaasApiKeyAuthentication


log = logging.getLogger(__name__)


class RunPlanResource(MongoEngineResource):

    class Meta:
        queryset = ApplicationRunPlan.objects.all()
        resource_name = 'run_plan'
        excludes = ['owner', 'current_package', 'packages']
        filtering = {
            'id': ALL,
            'application': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def obj_create(self, bundle, request=None, **kwargs):
        #FIXME handle reference field properly using mongoengine-tastypie
        log.debug(u"Going to create new run plan for user "
                  u"'%s'" % bundle.request.user.username)
        app = Application.objects(id=bundle.data['application']).first()
        if not app or not app.current_package:
            msg = u"Can't create new run plan, no packages built"
            log.warning(msg)
            raise exceptions.ValidationError(msg)

        bundle.data['application'] = app
        try:
            return super(MongoEngineResource, self).obj_create(
                bundle, request=request, **kwargs)
        except mongoengine.ValidationError, e:
            log.warning(u"Can't create new run plan, invalid data payload: "
                        "%s" % e.message)
            raise exceptions.ValidationError(e.message)
        except mongoengine.NotUniqueError:
            msg = u"Application '%s' is already " \
                  u"running" % bundle.data['application'].name
            log.warning(msg)
            raise exceptions.ValidationError(msg)

    def apply_authorization_limits(self, request, object_list):
        log.debug(u"Limiting query to user owned apps "
                  u"(length: %d)" % len(object_list))
        return object_list.filter(application=request.user.applications)
