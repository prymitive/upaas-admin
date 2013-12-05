# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from difflib import unified_diff

from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.http import Http404, HttpResponse, HttpResponseRedirect

from mongoengine.errors import ValidationError, DoesNotExist

from tabination.views import TabView

from pure_pagination import Paginator, PageNotAnInteger
from pure_pagination.mixins import PaginationMixin

from upaas.storage.utils import find_storage_handler

from upaas_admin.common.mixin import (
    LoginRequiredMixin, AppTemplatesDirMixin, DetailTabView, MongoDetailView)
from upaas_admin.apps.applications.mixin import (
    OwnedAppsMixin, OwnedPackagesMixin, OwnedAppTasksMixin, AppActionView)
from upaas_admin.apps.applications.models import Application, Package
from upaas_admin.apps.applications.forms import (
    RegisterApplicationForm, UpdateApplicationMetadataForm,
    UpdateApplicationMetadataInlineForm, BuildPackageForm, StopApplicationForm,
    RollbackApplicationForm, ApplicatiomMetadataFromPackageForm)
from upaas_admin.apps.scheduler.forms import (ApplicationRunPlanForm,
                                              EditApplicationRunPlanForm)
from upaas_admin.apps.applications.http import application_error
from upaas_admin.apps.tasks.constants import TaskStatus


log = logging.getLogger(__name__)


class IndexView(LoginRequiredMixin, OwnedAppsMixin, AppTemplatesDirMixin,
                PaginationMixin, TabView):

    template_name = 'index.html'
    paginate_by = 10
    _is_tab = True
    tab_id = 'site_index'
    tab_group = 'users_index'
    tab_label = _('Applications')

    def get(self, request, *args, **kwargs):
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        self.object_list = request.user.applications
        paginator = Paginator(self.object_list, self.paginate_by,
                              request=request)
        tasks = paginator.page(page)
        context = self.get_context_data(object_list=tasks.object_list,
                                        page_obj=tasks)
        return self.render_to_response(context)


class RegisterApplicationView(LoginRequiredMixin, AppTemplatesDirMixin,
                              TabView, CreateView):
    template_name = 'register.html'
    model = Application
    form_class = RegisterApplicationForm
    _is_tab = True
    tab_id = 'app_register'
    tab_group = 'users_index'
    tab_label = _('Register new application')
    weight = 99

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.metadata = form.cleaned_data['metadata']
        return super(RegisterApplicationView, self).form_valid(form)


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


class ApplicationPackagesView(LoginRequiredMixin, OwnedAppsMixin,
                              AppTemplatesDirMixin, PaginationMixin,
                              MongoDetailView, TabView):

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


class ApplicationTasksView(LoginRequiredMixin, OwnedAppsMixin,
                           AppTemplatesDirMixin, PaginationMixin,
                           MongoDetailView, DetailTabView):

    template_name = 'tasks.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    paginate_by = 10
    tab_id = 'app_tasks'
    tab_group = 'app_navigation'
    tab_label = _('Tasks')

    def get(self, request, *args, **kwargs):
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        self.object = self.get_object()
        self.object_list = self.object.tasks.order_by('-date_created',
                                                      'parent')
        paginator = Paginator(self.object_list, self.paginate_by,
                              request=request)
        tasks = paginator.page(page)
        context = self.get_context_data(object=self.object,
                                        tasks=tasks.object_list,
                                        task_statuses=TaskStatus,
                                        page_obj=tasks)
        return self.render_to_response(context)


class ApplicationTaskDetailsView(LoginRequiredMixin, OwnedAppTasksMixin,
                                 AppTemplatesDirMixin, MongoDetailView):

    template_name = 'task_details.html'
    slug_field = 'id'
    context_object_name = 'task'
    #TODO add support for virtual tasks


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

    def get(self, request, *args, **kwargs):
        self.app = self.get_object()
        if self.app.run_plan:
            return application_error(request, self.app,
                                     _(u"Application is already started"))
        elif not self.app.can_start:
            return application_error(request, self.app,
                                     _(u"Application cannot be started yet"))
        return super(StartApplicationView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.app = self.get_object()
        if self.app.run_plan:
            return application_error(request, self.app,
                                     _(u"Application is already started"))
        elif not self.app.can_start:
            return application_error(request, self.app,
                                     _(u"Application cannot be started yet"))
        return super(StartApplicationView, self).post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        try:
            return super(StartApplicationView, self).get_object(
                queryset=queryset)
        except (ValidationError, DoesNotExist):
            raise Http404

    def get_success_url(self):
        return reverse('app_instances', args=[self.app.safe_id])

    def get_context_data(self, **kwargs):
        context = super(StartApplicationView, self).get_context_data(**kwargs)
        context['app'] = self.app
        return context

    def get_form(self, form_class):
        form = super(StartApplicationView, self).get_form(form_class)
        form.user = self.request.user
        form.helper.form_action = reverse('app_start', args=[self.app.safe_id])
        return form

    def form_valid(self, form):
        form.instance.application = self.app
        form.instance.memory_per_worker = self.request.user.limits[
            'memory_per_worker']
        ret = super(StartApplicationView, self).form_valid(form)
        self.app.start_application()
        return ret


class EditApplicationRunPlanView(LoginRequiredMixin, OwnedAppsMixin,
                                 AppTemplatesDirMixin, UpdateView,
                                 SingleObjectMixin):
    template_name = 'edit_run_plan.html'
    model = Application
    form_class = EditApplicationRunPlanForm
    slug_field = 'id'
    context_object_name = 'app'

    def get(self, request, *args, **kwargs):
        self.app = self.get_object()
        if not self.app.run_plan:
            return application_error(request, self.app,
                                     _(u"Application is stopped"))
        return super(EditApplicationRunPlanView, self).get(request, *args,
                                                           **kwargs)

    def post(self, request, *args, **kwargs):
        self.app = self.get_object()
        if not self.app.run_plan:
            return application_error(request, self.app,
                                     _(u"Application is stopped"))
        return super(EditApplicationRunPlanView, self).post(request, *args,
                                                            **kwargs)

    def get_object(self, queryset=None):
        try:
            return super(EditApplicationRunPlanView, self).get_object(
                queryset=queryset)
        except (ValidationError, DoesNotExist):
            raise Http404

    def get_success_url(self):
        return reverse('app_instances', args=[self.app.safe_id])

    def get_context_data(self, **kwargs):
        context = super(EditApplicationRunPlanView, self).get_context_data(
            **kwargs)
        context['app'] = self.app
        return context

    def get_form_kwargs(self):
        ret = super(EditApplicationRunPlanView, self).get_form_kwargs()
        ret['instance'] = self.app.run_plan
        return ret

    def get_form(self, form_class):
        form = super(EditApplicationRunPlanView, self).get_form(form_class)
        form.user = self.request.user
        form.helper.form_action = reverse('app_edit_run_plan',
                                          args=[self.app.safe_id])
        return form

    def form_valid(self, form):
        form.instance.memory_per_worker = self.request.user.limits[
            'memory_per_worker']
        ret = super(EditApplicationRunPlanView, self).form_valid(form)
        self.app.update_application()
        return ret


class StopApplicationView(AppActionView):

    template_name = 'stop.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    form_class = StopApplicationForm

    def get_success_url(self):
        return reverse('app_instances', args=[self.object.safe_id])

    def validate_action(self, request):
        if not self.object.run_plan:
            return application_error(request, self.object,
                                     _(u"Application is already stopped"))

    def action(self, form):
        if self.object:
            self.object.stop_application()


class PackageDetailView(LoginRequiredMixin, OwnedPackagesMixin,
                        AppTemplatesDirMixin, MongoDetailView):

    template_name = 'package_details.html'
    model = Package
    slug_field = 'id'
    context_object_name = 'pkg'

    def get_context_data(self, **kwargs):
        context = super(PackageDetailView, self).get_context_data(**kwargs)
        if self.object:
            context['app'] = self.object.application
        context['metadiff'] = list(unified_diff(
            self.object.application.metadata.splitlines(1),
            self.object.metadata.splitlines(1), fromfile=__(u"Application"),
            tofile=__(u"Package")))
        return context


class PackageDeleteView(LoginRequiredMixin, OwnedPackagesMixin,
                        AppTemplatesDirMixin, DeleteView, MongoDetailView):
    template_name = 'delete_package.html'
    model = Package
    slug_field = 'id'
    context_object_name = 'pkg'
    success_url = reverse_lazy(ApplicationPackagesView.tab_id)

    def get_context_data(self, **kwargs):
        context = super(PackageDeleteView, self).get_context_data(**kwargs)
        if self.object:
            context['app'] = self.object.application
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.id != self.object.application.current_package.id:
            if self.object.filename:
                storage = find_storage_handler(self.upaas_config)
                if not storage:
                    log.error(_(u"Storage handler {name} not found").format(
                        name=self.upaas_config.storage.handler))
                    return application_error(request, self.object.application,
                                             _(u"Storage error, please try "
                                               u"again later"))
                if storage.exists(self.object.filename):
                    log.info(_(u"Removing package {pkg} file: {path}").format(
                        self.object.safe_id, self.object.filename))
                    storage.delete(self.object.filename)
            self.object.delete()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return application_error(request, self.object.application,
                                     _(u"Package in use"))


class BuildPackageView(AppActionView):

    template_name = 'build.html'
    model = Application
    slug_field = 'id'
    context_object_name = 'app'
    form_class = BuildPackageForm
    task = None

    def get_success_url(self):
        return reverse('app_task_details', args=[self.task.safe_id])

    def action(self, form):
        if self.object and self.object.metadata:
            self.task = self.object.build_package(
                force_fresh=form.cleaned_data['force_fresh'])


class RollbackApplicationView(OwnedPackagesMixin, AppActionView):

    template_name = 'rollback.html'
    model = Package
    slug_field = 'id'
    context_object_name = 'pkg'
    form_class = RollbackApplicationForm

    def get_success_url(self):
        return reverse('app_packages', args=[self.object.application.safe_id])

    def validate_action(self, request):
        if self.object == self.object.application.current_package:
            return application_error(
                request, self.object, _(u"Selected package is already current "
                                        u"for this application"))

    def action(self, form):
        if self.object:
            app = self.object.application
            app.current_package = self.object
            app.save()
            app.upgrade_application()


class ApplicatiomMetadataFromPackageView(OwnedPackagesMixin, AppActionView):

    template_name = 'app_meta_from_pkg.html'
    model = Package
    slug_field = 'id'
    context_object_name = 'pkg'
    form_class = ApplicatiomMetadataFromPackageForm

    def get_success_url(self):
        return reverse('app_metadata', args=[self.object.application.safe_id])

    def action(self, form):
        if self.object:
            app = self.object.application
            app.metadata = self.object.metadata
            app.save()


class DownloadApplicationMetadataView(LoginRequiredMixin, OwnedAppsMixin,
                                      MongoDetailView):

    model = Application
    slug_field = 'id'

    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(self.object.metadata,
                                content_type='text/x-yaml;charset=utf-8',
                                **response_kwargs)
        response['Content-Disposition'] = 'attachment; filename="%s' \
                                          '.yml"' % self.object.name
        return response


class DownloadPackageMetadataView(LoginRequiredMixin, OwnedPackagesMixin,
                                  MongoDetailView):

    model = Package
    slug_field = 'id'

    def render_to_response(self, context, **response_kwargs):
        response = HttpResponse(self.object.metadata,
                                content_type='text/x-yaml;charset=utf-8',
                                **response_kwargs)
        response[
            'Content-Disposition'] = 'attachment; filename="%s-%s.yml"' % (
            self.object.application.name, self.object.safe_id)
        return response
