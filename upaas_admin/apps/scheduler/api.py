# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

import mongoengine

from django.core import exceptions
from django.utils.translation import ugettext_lazy as _

from tastypie_mongoengine.resources import MongoEngineResource

from tastypie.resources import ALL
from tastypie.authorization import Authorization

from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.scheduler.forms import ApplicationRunPlanForm
from upaas_admin.common.apiauth import UpaasApiKeyAuthentication
from upaas_admin.common.api_validation import MongoCleanedDataFormValidation


log = logging.getLogger(__name__)


class RunPlanResource(MongoEngineResource):

    class Meta:
        queryset = ApplicationRunPlan.objects.all()
        resource_name = 'run_plan'
        excludes = ['backends', 'memory_per_worker']
        filtering = {
            'id': ALL,
            'application': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()
        validation = MongoCleanedDataFormValidation(
            form_class=ApplicationRunPlanForm)

    def __init__(self, *args, **kwargs):
        super(RunPlanResource, self).__init__(*args, **kwargs)
        self.fields['application'].readonly = True

    def obj_create(self, bundle, request=None, **kwargs):
        #FIXME handle reference field properly using mongoengine-tastypie
        log.debug(_(u"Going to create new run plan for user "
                  u"'{name}'").format(name=bundle.request.user.username))
        app = Application.objects(id=bundle.data['application'],
                                  owner=bundle.request.user).first()
        if not app or not app.current_package:
            msg = unicode(_(u"Can't create new run plan, app not found, or"
                            u" no packages built yet"))
            log.warning(msg)
            raise exceptions.ValidationError(msg)

        kwargs['application'] = app
        kwargs['memory_per_worker'] = bundle.request.user.limits[
            'memory_per_worker']
        try:
            return super(MongoEngineResource, self).obj_create(bundle,
                                                               request=request,
                                                               **kwargs)
        except mongoengine.ValidationError, e:
            log.warning(_(u"Can't create new run plan, invalid data payload: "
                        "{msg}").format(msg=e.message))
            raise exceptions.ValidationError(e.message)
        except mongoengine.NotUniqueError:
            msg = unicode(_(u"Application is already running"))
            log.warning(msg)
            raise exceptions.ValidationError(msg)

    def obj_update(self, bundle, **kwargs):
        bundle.obj.memory_per_worker = bundle.request.user.limits[
            'memory_per_worker']
        return super(RunPlanResource, self).obj_update(bundle, **kwargs)

    def apply_authorization_limits(self, request, object_list):
        log.debug(_(u"Limiting query to user owned apps (length: "
                    u"{length})").format(length=len(object_list)))
        return object_list.filter(application__in=request.user.applications)
