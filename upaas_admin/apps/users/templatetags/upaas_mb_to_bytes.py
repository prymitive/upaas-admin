# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import template


register = template.Library()


@register.filter
def mb_to_bytes(value):
    return value*1024*1024
