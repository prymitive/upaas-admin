# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import TemplateView

from upaas_admin.mixin import LoginRequiredMixin, MongoEngineViewMixin
from upaas_admin.apps.applications.models import Application


class IndexView(LoginRequiredMixin, MongoEngineViewMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['applications'] = Application.objects.filter(
            owner=self.request.user)
        return context
