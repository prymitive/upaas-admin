# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import DetailView

from upaas_admin.mixin import LoginRequiredMixin, MongoEngineViewMixin
from upaas_admin.apps.users.models import User


class UserProfileView(LoginRequiredMixin, MongoEngineViewMixin, DetailView):

    model = User
    template_name = "profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_object_name(self, obj):
        return self.request.user.username
