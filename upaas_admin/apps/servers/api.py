# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from tastypie_mongoengine.resources import MongoEngineResource

from tastypie.resources import ALL
from tastypie.authorization import Authorization

from upaas_admin.apps.servers.models import BackendServer, RouterServer
from upaas_admin.apiauth import UpaasApiKeyAuthentication


log = logging.getLogger(__name__)


class BackendResource(MongoEngineResource):

    class Meta:
        queryset = BackendServer.objects.all()
        resource_name = 'backend'
        filtering = {
            'id': ALL,
            'ip': ALL,
            'name': ALL,
        }
        always_return_data = True
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()


class RouterResource(MongoEngineResource):

    class Meta:
        queryset = RouterServer.objects.all()
        resource_name = 'router'
        filtering = {
            'id': ALL,
            'private_ip': ALL,
            'public_ip': ALL,
            'name': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()
