# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView, CreateView, UpdateView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from tabination.views import TabView

from pure_pagination import Paginator, PageNotAnInteger
from pure_pagination.mixins import PaginationMixin

from upaas_admin.common.mixin import (
    LoginRequiredMixin, AppTemplatesDirMixin, DetailTabView, MongoDetailView)
from upaas_admin.apps.applications.mixin import (
    OwnedAppsMixin, OwnedPackagesMixin, AppActionView)
from upaas_admin.apps.applications.models import Application, Package
from upaas_admin.apps.applications.forms import (
    RegisterApplicationForm, UpdateApplicationMetadataForm,
    UpdateApplicationMetadataInlineForm, BuildPackageForm, StopApplicationForm)
from upaas_admin.apps.scheduler.forms import ApplicationRunPlanForm


class IndexView(LoginRequiredMixin, OwnedAppsMixin, AppTemplatesDirMixin,
                PaginationMixin, ListView):

    template_name = 'index.html'
    paginate_by = 10


class ApplicationDetailView(LoginRequiredMixin, OwnedAppsMixin,
                            AppTemplatesDirMixin, MongoDetailView,
                            DetailTabView):

    template_name = 'details.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    tab_id = 'app_details'
    tab_group = 'app_navigation'
    tab_label = _('Details')


class ApplicationMetadataView(LoginRequiredMixin, OwnedAppsMixin,
                              AppTemplatesDirMixin, MongoDetailView,
                              DetailTabView):

    template_name = 'metadata.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    tab_id = 'app_metadata'
    tab_group = 'app_navigation'
    tab_label = _('Metadata')

    def get_context_data(self, **kwargs):
        context = super(ApplicationMetadataView, self).get_context_data(
            **kwargs)
        metadata_form = UpdateApplicationMetadataInlineForm()
        metadata_form.helper.form_action = reverse('app_update_metadata',
                                                   args=[self.object.safe_id])
        context['metadata_form'] = metadata_form
        return context


class ApplicationPackagesView(LoginRequiredMixin, AppTemplatesDirMixin,
                              PaginationMixin, MongoDetailView,
                              TabView):

    template_name = 'packages.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    paginate_by = 10
    _is_tab = True
    tab_id = 'app_packages'
    tab_group = 'app_navigation'
    tab_label = _('Packages')

    def get(self, request, *args, **kwargs):
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        self.object = self.get_object()
        self.object_list = Package.objects(application=self.object)
        paginator = Paginator(self.object_list, self.paginate_by,
                              request=request)
        packages = paginator.page(page)
        context = self.get_context_data(object=self.object,
                                        packages=packages.object_list,
                                        page_obj=packages)
        return self.render_to_response(context)


class ApplicationInstancesView(LoginRequiredMixin, OwnedAppsMixin,
                               AppTemplatesDirMixin, MongoDetailView,
                               DetailTabView):

    template_name = 'instances.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    tab_id = 'app_instances'
    tab_group = 'app_navigation'
    tab_label = _('Instances')


class RegisterApplicationView(LoginRequiredMixin, AppTemplatesDirMixin,
                              CreateView):
    template_name = 'register.html'
    model = Application
    form_class = RegisterApplicationForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.metadata = form.cleaned_data['metadata']
        return super(RegisterApplicationView, self).form_valid(form)


class UpdateApplicationMetadataView(LoginRequiredMixin, OwnedAppsMixin,
                                    AppTemplatesDirMixin, UpdateView):
    template_name = 'update_metadata.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    form_class = UpdateApplicationMetadataForm

    def get_success_url(self):
        return reverse('app_metadata', args=[self.object.safe_id])

    def form_valid(self, form):
        form.instance.metadata = form.cleaned_data['metadata']
        return super(UpdateApplicationMetadataView, self).form_valid(form)


class StartApplicationView(LoginRequiredMixin, OwnedAppsMixin,
                           AppTemplatesDirMixin, CreateView,
                           SingleObjectMixin):
    template_name = 'start.html'
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
        self.app.start_application()
        return ret


class PackageDetailView(LoginRequiredMixin, OwnedPackagesMixin,
                        AppTemplatesDirMixin, MongoDetailView):

    template_name = 'package_details.html'
    model = Package
    slug_field = 'id'
    context_object_name = 'pkg'


class BuildPackageView(AppActionView):

    template_name = 'build.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    form_class = BuildPackageForm

    def action(self, form):
        if self.object and self.object.metadata:
            self.object.build_package(
                force_fresh=form.cleaned_data['force_fresh'])


class StopApplicationView(AppActionView):

    template_name = 'stop.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    form_class = StopApplicationForm

    def action(self, form):
        if self.object:
            self.object.stop_application()
