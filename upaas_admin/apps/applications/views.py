# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView, DetailView

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import LoginRequiredMixin, AppTemplatesDirMixin
from upaas_admin.apps.applications.mixin import OwnedAppsMixin
from upaas_admin.apps.applications.models import Application


class IndexView(LoginRequiredMixin, OwnedAppsMixin, AppTemplatesDirMixin,
                PaginationMixin, ListView):

    template_name = 'index.haml'
    paginate_by = 10


class ApplicationDetailView(LoginRequiredMixin, OwnedAppsMixin,
                            AppTemplatesDirMixin, DetailView):

    template_name = 'details.haml'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
