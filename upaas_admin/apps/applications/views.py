# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import LoginRequiredMixin, MongoEngineViewMixin
from upaas_admin.apps.applications.models import Application


class IndexView(LoginRequiredMixin, MongoEngineViewMixin, PaginationMixin,
                ListView):

    template_name = 'index.haml'
    paginate_by = 10

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)
