# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


class ApplicationFlags(object):
    # building flags
    needs_building = 'NEEDS_BUILDING'
    is_building = 'IS_BUILDING'
    build_fresh_package = 'BUILD_FRESH_PACKAGE'
