# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from django.views.generic import TemplateView, FormView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from upaas_admin.common.mixin import LoginRequiredMixin, AppTemplatesDirMixin
from upaas_admin.apps.users.models import User
from upaas_admin.apps.users.forms import ResetApiKeyForm


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
        messages.error(self.request, _(u"Invalid form, possible bug"))
        return super(ResetApiKeyView, self).form_invalid(form)

    def form_valid(self, form):
        log.info(_(u"Resetting API key for") +
                 u" %s" % self.request.user.username)
        self.request.user.apikey = User.generate_apikey()
        self.request.user.save()
        messages.success(self.request, _(u"New API key generated"))
        return super(ResetApiKeyView, self).form_valid(form)
