# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView, DetailView, CreateView

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import LoginRequiredMixin, AppTemplatesDirMixin
from upaas_admin.apps.applications.mixin import OwnedAppsMixin
from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.applications.forms import RegisterApplicationForm


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


class RegisterApplicationView(LoginRequiredMixin, AppTemplatesDirMixin,
                              CreateView):
    template_name = 'register.haml'
    model = Application
    form_class = RegisterApplicationForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.metadata = form.cleaned_data['metadata']
        return super(RegisterApplicationView, self).form_valid(form)
