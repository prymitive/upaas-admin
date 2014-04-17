# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


class Flags(object):

    needs_building = 'NEEDS_BUILDING'
    is_building = 'IS_BUILDING'
    build_fresh_package = 'BUILD_FRESH_PACKAGE'
    build_interpreter_version = 'BUILD_INTERPRETER_VERSION'

    # instance management flags
    needs_stopping = 'NEEDS_STOPPING'
    needs_restart = 'NEEDS_RESTART'
