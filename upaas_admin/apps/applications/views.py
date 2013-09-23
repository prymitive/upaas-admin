# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView, DetailView, CreateView
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import LoginRequiredMixin, AppTemplatesDirMixin
from upaas_admin.apps.applications.mixin import OwnedAppsMixin
from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.applications.forms import RegisterApplicationForm
from upaas_admin.apps.scheduler.forms import ApplicationRunPlanForm


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


class StartApplicationView(LoginRequiredMixin, AppTemplatesDirMixin,
                           CreateView, SingleObjectMixin):
    template_name = 'start.haml'
    model = Application
    form_class = ApplicationRunPlanForm
    slug_field = 'id'
    context_object_name = 'app'

    def get_success_url(self):
        return reverse('app_details', args=[self.app.safe_id])

    def get_context_data(self, **kwargs):
        context = super(StartApplicationView, self).get_context_data(**kwargs)
        context['app'] = self.app
        return context

    def get_form(self, form_class):
        #TODO disallow to start if app already has run plan
        self.app = self.get_object()
        form = super(StartApplicationView, self).get_form(form_class)
        form.user = self.request.user
        form.helper.form_action = reverse('app_start', args=[self.app.safe_id])
        return form

    def form_valid(self, form):
        form.instance.application = self.app
        ret = super(StartApplicationView, self).form_valid(form)
        if not self.app.start_application():
            messages.error(self.request, _(u"Couldn't start application, no "
                                           u"backend available"))
            self.app.run_plan.delete()
        else:
            messages.success(self.request, _(u"Application started "
                                             u"successfully"))
        return ret
