# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from tastypie.exceptions import Unauthorized


class ReadOnlyResourceMixin:

    def create_list(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def create_detail(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def update_list(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def update_detail(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def delete_list(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))

    def delete_detail(self, object_list, bundle):
        raise Unauthorized(_("Unauthorized for such operation"))
