# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import inspect

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied


class AppTemplatesDirMixin(object):

    def get_template_names(self):
        app_name = os.path.basename(
            os.path.dirname(inspect.getfile(self.__class__)))
        return os.path.join(app_name, self.template_name)


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args,
                                                        **kwargs)


class SuperUserRequiredMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        return super(SuperUserRequiredMixin, self).dispatch(request, *args,
                                                            **kwargs)
