# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from django.conf.urls import url

from tastypie_mongoengine.resources import MongoEngineResource
from tastypie_mongoengine.fields import ReferenceField, EmbeddedListField

from tastypie.resources import ALL
from tastypie.authorization import Authorization
from tastypie.utils import trailing_slash

from upaas_admin.common.apiauth import UpaasApiKeyAuthentication
from upaas_admin.common.api import ReadOnlyResourceMixin
from upaas_admin.apps.tasks.models import Task, TaskMessage


log = logging.getLogger(__name__)


class TaskResource(MongoEngineResource, ReadOnlyResourceMixin):

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
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def dehydrate(self, bundle):
        bundle.data['icon_class'] = bundle.obj.icon_class
        bundle.data['is_running'] = bundle.obj.is_running
        bundle.data['is_failed'] = bundle.obj.is_failed
        bundle.data['is_successful'] = bundle.obj.is_successful
        bundle.data['is_finished'] = bundle.obj.is_finished
        return bundle

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/messages%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('messages'), name="messages"),
        ]

    def messages(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        try:
            offset = int(request.GET.get('offset', 0))
        except:
            offset = 0

        task = Task.objects(**self.remove_api_resource_names(kwargs)).first()
        messages = []
        for msg in task.messages[int(offset):]:
            messages.append({
                'id': msg.timestamp.isoformat(),
                'timestamp': msg.timestamp.isoformat(),
                'level': logging.getLevelName(msg.level),
                'message': msg.message,
            })
        resp = {
            'meta': {
                'limit': 0,
                'next': None,
                'offset': 0,
                'previous': None,
                'total_count': len(messages),
            },
            'objects': messages,
        }
        return self.create_response(request, resp)
