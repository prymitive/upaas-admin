# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas_admin.apps.servers.models import BackendServer


def select_best_backend():
    """
    Return backend server that is the least loaded one or None if there is no
    enabled backend.
    """
    #FIXME make it aware of each backend resources
    scores = {}
    for backend in BackendServer.objects(is_enabled=True):
        for run_plan in backend.run_plans:
            scores = dict(scores.items() +
                          {backend: run_plan.memory_limit}.items())
    if scores:
        score = sorted(scores.values())[0]
        for (backend, backend_score) in scores.items():
            if score == backend_score:
                return backend
    else:
        # no run plans, just return first backend
        return BackendServer.objects(is_enabled=True).first()
