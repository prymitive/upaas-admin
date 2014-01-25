# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.contrib.auth.views import password_reset_confirm
from django.http import Http404

from mongoengine import ValidationError


def safe_password_reset_confirm(*args, **kwargs):
    """
    If uidb64 value is invalid mongoengine seems to get unsafe value for user
    id and raises ValidationError.
    """
    try:
        return password_reset_confirm(*args, **kwargs)
    except ValidationError:
        raise Http404
