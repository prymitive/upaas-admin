# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView, DetailView

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import LoginRequiredMixin, MongoEngineViewMixin
from upaas_admin.apps.applications.mixin import OwnedAppsMixin
from upaas_admin.apps.applications.models import Application


class IndexView(LoginRequiredMixin, MongoEngineViewMixin, PaginationMixin,
                OwnedAppsMixin, ListView):

    template_name = 'index.haml'
    paginate_by = 10


class ApplicationDetailView(LoginRequiredMixin, MongoEngineViewMixin,
                            OwnedAppsMixin, DetailView):

    template_name = 'details.haml'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
