# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import inspect

from tabination.views import TabView

from mongoengine.errors import ValidationError, DoesNotExist

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView
from django.http import Http404


class AppTemplatesDirMixin(object):

    def get_template_names(self):
        app_name = os.path.basename(
            os.path.dirname(inspect.getfile(self.__class__)))
        return os.path.join(app_name, self.template_name)


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args,
                                                        **kwargs)


class SuperUserRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        return super(SuperUserRequiredMixin, self).dispatch(request, *args,
                                                            **kwargs)


class DetailTabView(TabView):

    _is_tab = True

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class MongoDetailView(DetailView):

    def get_object(self, queryset=None):
        try:
            return super(MongoDetailView, self).get_object(queryset=queryset)
        except (ValidationError, DoesNotExist):
            raise Http404
