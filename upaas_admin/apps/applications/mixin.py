# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import FormView
from django.core.urlresolvers import reverse

from upaas_admin.apps.applications.models import Application, Package
from upaas_admin.common.mixin import (LoginRequiredMixin, AppTemplatesDirMixin,
                                      MongoDetailView)


class OwnedAppsMixin(object):
    """
    Limits query to applications owned by current user.
    """

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)


class OwnedPackagesMixin(object):
    """
    Limits query to packages belonging to apps owned by current user.
    """

    def get_queryset(self):
        return Package.objects.filter(
            application__in=Application.objects.filter(
                owner=self.request.user))


class AppActionView(LoginRequiredMixin, OwnedAppsMixin, AppTemplatesDirMixin,
                    MongoDetailView, FormView):

    def get_success_url(self):
        return reverse('app_details', args=[self.object.safe_id])

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(AppActionView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.action(form)
        return super(AppActionView, self).form_valid(form)

    def action(self, form):
        pass
