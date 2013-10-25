# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from json import dumps

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from dajaxice.decorators import dajaxice_register

from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.servers.constants import PortsNames
from upaas_admin.common.uwsgi import fetch_json_stats


@login_required
@dajaxice_register
def stop_app(request, app_id):
    app = Application.objects.filter(id=app_id, owner=request.user).first()
    if app and app.metadata:
        app.stop_application()
    return dumps({})


@login_required
@dajaxice_register
@cache_page(3)  # TODO make it configurable?
def stats(request, app_id):
    data = []
    app = Application.objects.filter(id=app_id, owner=request.user).first()
    if app.run_plan:
        for backend in app.run_plan.backends:
            ports_data = backend.application_ports(app)
            if ports_data and ports_data.ports.get(PortsNames.stats):
                s = fetch_json_stats(str(backend.ip),
                                     ports_data.ports[PortsNames.stats])
                if s:
                    data.append(
                        {'backend': {'name': backend.name,
                                     'ip': str(backend.ip)},
                         'stats': s})
    return dumps({'stats': data})
