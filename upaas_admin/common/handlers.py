# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import RequestContext, Context
from functools import partial


# code from https://forrst.com/posts/Django_404_and_500_with_RequestContext-m8U
def base_error(request, status=500, template_name=None):
    try:
        context = RequestContext(request)
    except Exception as e:
        context = Context()
    return HttpResponse(
        content=render_to_string(template_name, context_instance=context),
        status=status)


bad_request = partial(base_error, status=400, template_name='400.html')
access_denied = partial(base_error, status=403, template_name='403.html')
page_not_found = partial(base_error, status=404, template_name='404.html')
server_error = partial(base_error, status=500, template_name='500.html')
