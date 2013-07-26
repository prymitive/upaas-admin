# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import ListView, UpdateView, CreateView
from django.core.urlresolvers import reverse_lazy

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import (LoginRequiredMixin, SuperUserRequiredMixin,
                               AppTemplatesDirMixin)
from upaas_admin.apps.users.models import User
from upaas_admin.apps.servers.models import RouterServer, BackendServer
from upaas_admin.apps.admin.forms import *


class AdminCreateUserView(LoginRequiredMixin, SuperUserRequiredMixin,
                          AppTemplatesDirMixin, CreateView):
    template_name = 'create_user.haml'
    model = User
    slug_field = 'username'
    success_url = reverse_lazy('admin_users_list')
    form_class = AdminCreateUserForm


class AdminEditUserView(LoginRequiredMixin, SuperUserRequiredMixin,
                        AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_user.haml'
    model = User
    slug_field = 'username'
    success_url = reverse_lazy('admin_users_list')
    form_class = AdminEditUserForm


class AdminUserListView(LoginRequiredMixin, SuperUserRequiredMixin,
                        AppTemplatesDirMixin, PaginationMixin, ListView):
    template_name = 'user_list.haml'
    paginate_by = 10
    model = User


class AdminCreateRouterView(LoginRequiredMixin, SuperUserRequiredMixin,
                            AppTemplatesDirMixin, CreateView):
    template_name = 'create_router.haml'
    model = RouterServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_routers_list')
    form_class = AdminRouterForm


class AdminEditRouterView(LoginRequiredMixin, SuperUserRequiredMixin,
                          AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_router.haml'
    model = RouterServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_routers_list')
    form_class = AdminRouterForm


class AdminRouterListView(LoginRequiredMixin, SuperUserRequiredMixin,
                          AppTemplatesDirMixin, PaginationMixin, ListView):
    template_name = 'router_list.haml'
    paginate_by = 10
    model = RouterServer


class AdminCreateBackendView(LoginRequiredMixin, SuperUserRequiredMixin,
                             AppTemplatesDirMixin, CreateView):
    template_name = 'create_backend.haml'
    model = BackendServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_backends_list')
    form_class = AdminBackendForm


class AdminEditBackendView(LoginRequiredMixin, SuperUserRequiredMixin,
                           AppTemplatesDirMixin, UpdateView):
    template_name = 'edit_backend.haml'
    model = BackendServer
    slug_field = 'name'
    success_url = reverse_lazy('admin_backends_list')
    form_class = AdminBackendForm


class AdminBackendListView(LoginRequiredMixin, SuperUserRequiredMixin,
                           AppTemplatesDirMixin, PaginationMixin, ListView):
    template_name = 'backend_list.haml'
    paginate_by = 10
    model = BackendServer
