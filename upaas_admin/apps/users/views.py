# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging

from django.views.generic import TemplateView, FormView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.http import Http404

from pure_pagination import Paginator, PageNotAnInteger, EmptyPage
from pure_pagination.mixins import PaginationMixin

from tabination.views import TabView

from upaas_admin.common.mixin import LoginRequiredMixin, AppTemplatesDirMixin
from upaas_admin.apps.users.models import User
from upaas_admin.apps.users.forms import ResetApiKeyForm
from upaas_admin.apps.tasks.constants import TaskStatus


log = logging.getLogger(__name__)


class UserProfileView(LoginRequiredMixin, AppTemplatesDirMixin, TemplateView):
    template_name = "profile.html"


class ResetApiKeyView(LoginRequiredMixin, AppTemplatesDirMixin, FormView):
    template_name = 'apikey_reset.html'
    form_class = ResetApiKeyForm
    success_url = reverse_lazy('users_profile')

    def get_initial(self):
        return {'apikey': self.request.user.apikey}

    def get_form(self, form_class):
        form = super(ResetApiKeyView, self).get_form(form_class)
        form._current_apikey = self.request.user.apikey
        return form

    def form_invalid(self, form):
        messages.error(self.request, _("Invalid form, possible bug"))
        return super(ResetApiKeyView, self).form_invalid(form)

    def form_valid(self, form):
        log.info(_("Resetting API key for {login}").format(
            login=self.request.user.username))
        self.request.user.apikey = User.generate_apikey()
        self.request.user.save()
        messages.success(self.request, _("New API key generated"))
        return super(ResetApiKeyView, self).form_valid(form)


class UserTasksView(LoginRequiredMixin, AppTemplatesDirMixin, PaginationMixin,
                    TabView):

    template_name = 'tasks.html'
    paginate_by = 10
    _is_tab = True
    tab_id = 'users_tasks'
    tab_group = 'users_index'
    tab_label = _('Tasks')

    def get(self, request, *args, **kwargs):
        self.object_list = request.user.tasks.order_by('-date_created',
                                                       'parent')
        paginator = Paginator(self.object_list, self.paginate_by,
                              request=request)
        try:
            tasks = paginator.page(request.GET.get('page', 1))
        except PageNotAnInteger:
            tasks = paginator.page(1)
        except EmptyPage:
            raise Http404
        context = self.get_context_data(tasks=tasks.object_list,
                                        task_statuses=TaskStatus,
                                        page_obj=tasks)
        return self.render_to_response(context)


class UserLimitsView(LoginRequiredMixin, AppTemplatesDirMixin, TabView):

    template_name = "limits.html"
    _is_tab = True
    tab_id = 'users_limits'
    tab_group = 'users_index'
    tab_label = _('Quota')
