# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

import mongoengine

from django.core import exceptions
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _

from tastypie_mongoengine.resources import MongoEngineResource
from tastypie_mongoengine.fields import ReferenceField, ReferencedListField

from tastypie.resources import ALL
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from tastypie.utils import trailing_slash

from upaas_admin.apps.applications.models import Application, Package
from upaas_admin.common.apiauth import UpaasApiKeyAuthentication
from upaas_admin.common.api import ReadOnlyResourceMixin

log = logging.getLogger(__name__)


class ApplicationResource(MongoEngineResource):

    current_package = ReferenceField(
        'upaas_admin.apps.applications.api.PackageResource', 'current_package',
        full=True, null=True, readonly=True)
    packages = ReferencedListField(
        'upaas_admin.apps.applications.api.PackageResource', 'packages',
        null=True, readonly=True)
    tasks = ReferencedListField('upaas_admin.apps.tasks.api.TaskResource',
                                'tasks', null=True, readonly=True)
    running_tasks = ReferencedListField(
        'upaas_admin.apps.tasks.api.TaskResource', 'running_tasks', null=True,
        readonly=True)

    class Meta:
        always_return_data = True
        queryset = Application.objects.all()
        resource_name = 'application'
        filtering = {
            'id': ALL,
            'name': ALL,
            'owner': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def __init__(self, *args, **kwargs):
        super(ApplicationResource, self).__init__(*args, **kwargs)
        self.fields['owner'].readonly = True

    def obj_create(self, bundle, request=None, **kwargs):
        log.debug(_("Going to create new application for user "
                    "'{name}'").format(name=bundle.request.user.username))
        try:
            return super(MongoEngineResource, self).obj_create(
                bundle, request=request, owner=bundle.request.user, **kwargs)
        except mongoengine.ValidationError as e:
            log.warning(_("Can't create new application, invalid data "
                          "payload: {msg}").format(msg=e.message))
            raise exceptions.ValidationError(e.message)
        except mongoengine.NotUniqueError as e:
            log.warning(_("Can't create new application, duplicated fields: "
                          "{msg}").format(msg=e.message))
            raise exceptions.ValidationError(e.message)

    def authorized_read_list(self, object_list, bundle):
        log.debug(_("Limiting query to user owned apps (length: "
                    "{length})").format(length=len(object_list)))
        return object_list.filter(owner=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return bundle.obj.owner == bundle.request.user

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return bundle.obj.owner == bundle.request.user

    def update_list(self, object_list, bundle):
        allowed = []
        for obj in object_list:
            if bundle.obj.owner == bundle.request.user:
                allowed.append(obj)
        return allowed

    def update_detail(self, object_list, bundle):
        return bundle.obj.owner == bundle.request.user

    def delete_list(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def delete_detail(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/build%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('build_package'), name="build"),
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/start%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('start_application'), name="start"),
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/stop%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('stop_application'), name="stop"),
            url(r"^(?P<resource_name>%s)/(?P<id>\w[\w/-]*)/update%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('update_application'), name="update"),
        ]

    def build_package(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        try:
            force_fresh = bool(int(request.GET.get('force_fresh', 0)))
        except:
            force_fresh = False
        interpreter_version = request.GET.get('interpreter_version') or None
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.metadata:
                return self.create_response(request, app.build_package(
                    force_fresh=force_fresh,
                    interpreter_version=interpreter_version))
            else:
                return HttpResponseBadRequest(
                    _("No metadata registered for app '{name}' with id "
                      "'{id}'").format(name=app.name, id=app.id))
        else:
            return HttpResponseNotFound(_("No such application"))

    def start_application(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.metadata and app.current_package:
                return self.create_response(request, app.start_application())
            else:
                return HttpResponseBadRequest(
                    _("No package built or no metadata registered for app "
                      "'{name}' with id '{id}'").format(name=app.name,
                                                        id=app.id))
        else:
            return HttpResponseNotFound(_("No such application"))

    def stop_application(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if not app.run_plan:
                return HttpResponseBadRequest(_(
                    "Application is already stopped"))
            if app.metadata and app.current_package:
                return self.create_response(request, app.stop_application())
            else:
                return HttpResponseBadRequest(
                    _("No package built or no metadata registered for app "
                      "'{name}' with id '{id}'").format(name=app.name,
                                                        id=app.id))
        else:
            return HttpResponseNotFound(_("No such application"))

    def update_application(self, request, **kwargs):
        self.method_check(request, allowed=['put'])
        app = Application.objects(
            **self.remove_api_resource_names(kwargs)).first()
        if app:
            if app.run_plan:
                return self.create_response(request, app.update_application())
            else:
                return HttpResponseBadRequest(_("Application is stopped"))
        else:
            return HttpResponseNotFound(_("No such application"))


class PackageResource(MongoEngineResource, ReadOnlyResourceMixin):

    application = ReferenceField(
        'upaas_admin.apps.applications.api.ApplicationResource', 'application')

    class Meta:
        always_return_data = True
        queryset = Package.objects.all()
        resource_name = 'package'
        filtering = {
            'id': ALL,
        }
        authentication = UpaasApiKeyAuthentication()
        authorization = Authorization()

    def authorized_read_list(self, object_list, bundle):
        log.debug(_("Limiting query to user owned apps (length: "
                    "{length})").format(length=len(object_list)))
        return object_list.filter(
            application__in=bundle.request.user.applications)

    def read_detail(self, object_list, bundle):
        return bundle.obj.application.owner == bundle.request.user
