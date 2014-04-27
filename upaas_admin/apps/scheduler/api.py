# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

import mongoengine

from django.core import exceptions
from django.utils.translation import ugettext as _

from tastypie_mongoengine.resources import MongoEngineResource

from tastypie.resources import ALL
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.scheduler.forms import ApplicationRunPlanForm
from upaas_admin.common.apiauth import UpaasApiKeyAuthentication
from upaas_admin.common.api_validation import MongoCleanedDataFormValidation


log = logging.getLogger(__name__)


class RunPlanResource(MongoEngineResource):

    class Meta:
        always_return_data = True
        queryset = ApplicationRunPlan.objects.all()
        resource_name = 'run_plan'
        excludes = ['backends', 'memory_per_worker', 'max_log_size']
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
        # FIXME handle reference field properly using mongoengine-tastypie
        log.debug(_("Going to create new run plan for user "
                    "'{name}'").format(name=bundle.request.user.username))
        app = Application.objects(id=bundle.data['application'],
                                  owner=bundle.request.user).first()
        if not app or not app.current_package:
            msg = _("Can't create new run plan, app not found, or no packages "
                    "built yet")
            log.warning(msg)
            raise exceptions.ValidationError(msg)

        kwargs['application'] = app
        kwargs['memory_per_worker'] = bundle.request.user.limits[
            'memory_per_worker']
        kwargs['max_log_size'] = bundle.request.user.limits['max_log_size']
        try:
            return super(MongoEngineResource, self).obj_create(bundle,
                                                               request=request,
                                                               **kwargs)
        except mongoengine.ValidationError as e:
            log.warning(_("Can't create new run plan, invalid data payload: "
                          "{msg}").format(msg=e.message))
            raise exceptions.ValidationError(e.message)
        except mongoengine.NotUniqueError:
            msg = str(_("Application is already running"))
            log.warning(msg)
            raise exceptions.ValidationError(msg)

    def obj_update(self, bundle, **kwargs):
        bundle.obj.memory_per_worker = bundle.request.user.limits[
            'memory_per_worker']
        bundle.obj.max_log_size = bundle.request.user.limits['max_log_size']
        return super(RunPlanResource, self).obj_update(bundle, **kwargs)

    def authorized_read_list(self, object_list, bundle):
        log.debug(_("Limiting query to user owned apps (length: "
                    "{length})").format(length=len(object_list)))
        return object_list.filter(
            application__in=bundle.request.user.applications)

    def read_detail(self, object_list, bundle):
        return bundle.obj.application.owner == bundle.request.user

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return bundle.obj.application.owner == bundle.request.user

    def update_list(self, object_list, bundle):
        allowed = []
        for obj in object_list:
            if bundle.obj.application.owner == bundle.request.user:
                allowed.append(obj)
        return allowed

    def update_detail(self, object_list, bundle):
        return bundle.obj.owner == bundle.request.user

    def delete_list(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def delete_detail(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))
