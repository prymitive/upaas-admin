# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.views.generic import DetailView

from upaas_admin.apps.users.models import User


class AboutView(DetailView):

    model = User
    template_name = "profile.html"
