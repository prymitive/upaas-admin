# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.http import Http404

from pure_pagination.mixins import PaginationMixin

from upaas_admin.common.mixin import (
    LoginRequiredMixin, SuperUserRequiredMixin, AppTemplatesDirMixin)
from upaas_admin.apps.users.models import User
from upaas_admin.apps.servers.models import RouterServer, BackendServer
from upaas_admin.apps.scheduler.models import UserLimits
from upaas_admin.apps.admin.forms import (AdminCreateUserForm,
                                          AdminEditUserForm, AdminRouterForm,
                                          AdminBackendForm,
                                          AdminUserLimitsForm)


class AdminCreateUserView(LoginRequiredMixin, SuperUserRequiredMixin,
                          AppTemplatesDirMixin, CreateView):
    template_name = 'create_user.html'
    model = User
    success_url = reverse_lazy('admin_users_list')
    form_class = AdminCreateUserForm


class AdminEditUserView(LoginRequiredMixin, SuperUserRequiredMixin,
                        AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_user.html'
    model = User
    slug_field = 'id'
    success_url = reverse_lazy('admin_users_list')
    form_class = AdminEditUserForm


class AdminCreateUserLimitsView(LoginRequiredMixin, SuperUserRequiredMixin,
                                AppTemplatesDirMixin, CreateView):
    template_name = 'create_user_limits.html'
    model = UserLimits
    success_url = reverse_lazy('admin_users_list')
    form_class = AdminUserLimitsForm

    def get(self, request, *args, **kwargs):
        self.limit_user = User.objects(id=kwargs['slug']).first()
        if not self.limit_user:
            raise Http404
        return super(AdminCreateUserLimitsView, self).get(request, *args,
                                                          **kwargs)

    def post(self, request, *args, **kwargs):
        self.limit_user = User.objects(id=kwargs['slug']).first()
        if not self.limit_user:
            raise Http404
        return super(AdminCreateUserLimitsView, self).post(request, *args,
                                                           **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AdminCreateUserLimitsView, self).get_context_data(
            **kwargs)
        context['limit_user'] = self.limit_user
        return context

    def get_initial(self):
        return UserLimits.get_default_limits()

    def form_valid(self, form):
        form.instance.user = self.limit_user
        return super(AdminCreateUserLimitsView, self).form_valid(form)


class AdminEditUserLimitsView(LoginRequiredMixin, SuperUserRequiredMixin,
                              AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_user_limits.html'
    model = UserLimits
    slug_field = 'id'
    success_url = reverse_lazy('admin_users_list')
    form_class = AdminUserLimitsForm
    #FIXME handle case when user is using more than we set here


class AdminDeleteUserLimitsView(LoginRequiredMixin, SuperUserRequiredMixin,
                                AppTemplatesDirMixin, DeleteView):
    template_name = 'delete_user_limits.html'
    model = UserLimits
    slug_field = 'id'
    success_url = reverse_lazy('admin_users_list')
    #FIXME handle case when user is using more than defaults


class AdminUserListView(LoginRequiredMixin, SuperUserRequiredMixin,
                        AppTemplatesDirMixin, PaginationMixin, ListView):
    template_name = 'user_list.html'
    paginate_by = 10
    model = User


class AdminCreateRouterView(LoginRequiredMixin, SuperUserRequiredMixin,
                            AppTemplatesDirMixin, CreateView):
    template_name = 'create_router.html'
    model = RouterServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_routers_list')
    form_class = AdminRouterForm


class AdminEditRouterView(LoginRequiredMixin, SuperUserRequiredMixin,
                          AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_router.html'
    model = RouterServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_routers_list')
    form_class = AdminRouterForm


class AdminRouterListView(LoginRequiredMixin, SuperUserRequiredMixin,
                          AppTemplatesDirMixin, PaginationMixin, ListView):
    template_name = 'router_list.html'
    paginate_by = 10
    model = RouterServer


class AdminCreateBackendView(LoginRequiredMixin, SuperUserRequiredMixin,
                             AppTemplatesDirMixin, CreateView):
    template_name = 'create_backend.html'
    model = BackendServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_backends_list')
    form_class = AdminBackendForm


class AdminEditBackendView(LoginRequiredMixin, SuperUserRequiredMixin,
                           AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_backend.html'
    model = BackendServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_backends_list')
    form_class = AdminBackendForm


class AdminBackendListView(LoginRequiredMixin, SuperUserRequiredMixin,
                           AppTemplatesDirMixin, PaginationMixin, ListView):
    template_name = 'backend_list.html'
    paginate_by = 10
    model = BackendServer
