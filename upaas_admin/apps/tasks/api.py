# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from tastypie_mongoengine.resources import MongoEngineResource
from tastypie_mongoengine.fields import ReferenceField

from tastypie.resources import ALL
from tastypie.authorization import Authorization

from upaas_admin.common.apiauth import UpaasApiKeyAuthentication
from upaas_admin.apps.tasks.models import Task


log = logging.getLogger(__name__)


class TaskResource(MongoEngineResource):

    application = ReferenceField(
        'upaas_admin.apps.applications.api.ApplicationResource', 'application')
    backend = ReferenceField('upaas_admin.apps.servers.api.BackendResource',
                             'backend')

    class Meta:
        always_return_data = True
        queryset = Task.objects.all()
        resource_name = 'task'
        excludes = ['messages']
        filtering = {
            'id': ALL,
            'application': ALL,
            'status': ALL,
        }
        always_return_data = True
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def dehydrate(self, bundle):
        bundle.data['icon_class'] = bundle.obj.icon_class
        bundle.data['is_running'] = bundle.obj.is_running
        bundle.data['is_failed'] = bundle.obj.is_failed
        bundle.data['is_successful'] = bundle.obj.is_successful
        bundle.data['is_finished'] = bundle.obj.is_finished
        return bundle
