# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas_admin.features.base import Feature


class StorageFeature(Feature):

    def update_vassal(self, options):
        app_dir = ''
        mountpoint = ''
        options.append('namespace-keep-mount = %s:%s' % (app_dir, mountpoint))
        return options
