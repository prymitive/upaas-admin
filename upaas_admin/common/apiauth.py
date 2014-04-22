# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from tastypie.authentication import Authentication

from upaas_admin.apps.users.models import User


class UpaasApiKeyAuthentication(Authentication):

    @staticmethod
    def get_user(request):
        if request.user.is_authenticated():
            return request.user
        apikey = request.META.get('HTTP_X_UPAAS_APIKEY')
        login = request.META.get('HTTP_X_UPAAS_LOGIN')
        return User.objects.filter(username=login, apikey=apikey,
                                   is_active=True).first()

    def is_authenticated(self, request, **kwargs):
        user = self.get_user(request)
        if user:
            request.user = user
            return True
        return False

    def get_identifier(self, request):
        user = self.get_user(request)
        if user:
            return user.username
        return 'anonymous'
