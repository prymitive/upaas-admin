# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django import template


register = template.Library()


@register.filter()
def inline_truncate(value, size):
    """
    Truncates a string to the given size placing the ellipsis at the middle
    of the string.

    Code from: https://djangosnippets.org/snippets/860/
    """
    if len(value) > size > 4:
        start = (size - 3) / 2
        end = (size - 3) - start
        return value[0:start] + '...' + value[-end:]
    else:
        return value[0:size]
