# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.shortcuts import render_to_response
from django.template import RequestContext, Context
from functools import partial


# code from https://forrst.com/posts/Django_404_and_500_with_RequestContext-m8U
def base_error(request, template_name=None):
    try:
        context = RequestContext(request)
    except Exception, e:
        context = Context()
    return render_to_response(template_name, context_instance=context)


bad_request = partial(base_error, template_name='400.html')
access_denied = partial(base_error, template_name='403.html')
page_not_found = partial(base_error, template_name='404.html')
server_error = partial(base_error, template_name='500.html')
