# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.http import HttpResponse
from django.template import RequestContext, loader


def application_error(request, app, error, status=406):
    template = loader.get_template('applications/error.html')
    context = RequestContext(request, {'app': app, 'error': error,
                                       'status_code': status})
    return HttpResponse(template.render(context), status=status)
