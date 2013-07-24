# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from django.views.generic import ListView, UpdateView, CreateView
from django.core.urlresolvers import reverse_lazy

from pure_pagination.mixins import PaginationMixin

from upaas_admin.mixin import (LoginRequiredMixin, SuperUserRequiredMixin,
                               AppTemplatesDirMixin)
from upaas_admin.apps.users.models import User
from upaas_admin.apps.admin.forms import AdminCreateUserForm, AdminEditUserForm


log = logging.getLogger(__name__)


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
