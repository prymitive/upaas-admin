# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

import mongoengine

from django.core import exceptions
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.conf.urls import url

from tastypie_mongoengine.resources import MongoEngineResource

from tastypie.resources import ALL
from tastypie.authorization import Authorization
from tastypie.utils import trailing_slash

from upaas_admin.apps.applications.models import Application, Package
from upaas_admin.apiauth import UpaasApiKeyAuthentication


log = logging.getLogger(__name__)


class ApplicationResource(MongoEngineResource):

    class Meta:
        queryset = Application.objects.all()
        resource_name = 'application'
        excludes = ['owner', 'current_package', 'packages']
        filtering = {
            'id': ALL,
            'name': ALL,
            'owner': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def dehydrate(self, bundle):
        bundle.data['packages'] = len(bundle.obj.packages)
        return bundle

    def obj_create(self, bundle, request=None, **kwargs):
        log.debug(u"Going to create new application for user "
                  u"'%s'" % bundle.request.user.username)
        try:
            return super(MongoEngineResource, self).obj_create(
                bundle, request=request, owner=bundle.request.user, **kwargs)
        except mongoengine.ValidationError, e:
            log.warning(u"Can't create new application, invalid data payload: "
                        "%s" % e.message)
            raise exceptions.ValidationError(e.message)
        except mongoengine.NotUniqueError, e:
            log.warning(u"Can't create new application, duplicated fields: "
                        "%s" % e.message)
            raise exceptions.ValidationError(e.message)

    def apply_authorization_limits(self, request, object_list):
        log.debug(u"Limiting query to user owned apps "
                  u"(length: %d)" % len(object_list))
        return object_list.filter(owner=request.user)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/build%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('build_package'), name="build"),
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/build_fresh%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('build_fresh_package'), name="build_fresh"),
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/start%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('start_application'), name="start"),
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/stop%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('stop_application'), name="stop"),
        ]

    def build_package(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.metadata:
                return self.create_response(
                    request, app.build_package())
            else:
                return HttpResponseBadRequest(
                    "No metadata registered for app '%s' with id '%s'" % (
                        app.name, app.id))
        else:
            return HttpResponseNotFound("No such application")

    def build_fresh_package(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.metadata:
                return self.create_response(
                    request, app.build_package(force_fresh=True))
            else:
                return HttpResponseBadRequest(
                    "No metadata registered for app '%s' with id '%s'" % (
                        app.name, app.id))
        else:
            return HttpResponseNotFound("No such application")

    def start_application(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.metadata and app.current_package:
                return self.create_response(
                    request, app.start_application())
            else:
                return HttpResponseBadRequest(
                    "No package built or no metadata registered for app '%s' "
                    "with id '%s'" % (app.name, app.id))
        else:
            return HttpResponseNotFound("No such application")

    def stop_application(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.metadata and app.current_package:
                return self.create_response(
                    request, app.stop_application())
            else:
                return HttpResponseBadRequest(
                    "No package built or no metadata registered for app '%s' "
                    "with id '%s'" % (app.name, app.id))
        else:
            return HttpResponseNotFound("No such application")


class PackageResource(MongoEngineResource):

    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        filtering = {
            'id': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()
