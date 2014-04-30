# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpForbidden

from django.utils.translation import ugettext_lazy as _


class ReadOnlyResourceMixin:

    def create_list(self, object_list, bundle):
        raise ImmediateHttpResponse(
            response=HttpForbidden(_("Unauthorized for such operation")))

    def create_detail(self, object_list, bundle):
        raise ImmediateHttpResponse(
            response=HttpForbidden(_("Unauthorized for such operation")))

    def update_list(self, object_list, bundle):
        raise ImmediateHttpResponse(
            response=HttpForbidden(_("Unauthorized for such operation")))

    def update_detail(self, object_list, bundle):
        raise ImmediateHttpResponse(
            response=HttpForbidden(_("Unauthorized for such operation")))

    def delete_list(self, request, **kwargs):
        raise ImmediateHttpResponse(
            response=HttpForbidden(_("Unauthorized for such operation")))

    def delete_detail(self, request, **kwargs):
        raise ImmediateHttpResponse(
            response=HttpForbidden(_("Unauthorized for such operation")))
