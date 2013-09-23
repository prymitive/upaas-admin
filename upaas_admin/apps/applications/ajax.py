# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from json import dumps

from django.contrib.auth.decorators import login_required

from dajaxice.decorators import dajaxice_register

from upaas_admin.apps.applications.models import Application


@login_required
@dajaxice_register
def build_package(request, app_id):
    task_id = None
    app = Application.objects.filter(id=app_id, owner=request.user).first()
    if app and app.metadata:
        task_id = app.build_package()
    return dumps({'task_id': task_id})


@login_required
@dajaxice_register
def stop_app(request, app_id):
    app = Application.objects.filter(id=app_id, owner=request.user).first()
    if app and app.metadata:
        app.stop_application()
    return dumps({})
