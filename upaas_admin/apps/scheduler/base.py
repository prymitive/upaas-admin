# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from upaas_admin.apps.servers.models import BackendServer


log = logging.getLogger(__name__)


def select_best_backend(exclude=[]):
    """
    Return backend server that is the least loaded one or None if there is no
    enabled backend.
    """
    #FIXME make it aware of each backend resources
    scores = {}
    for backend in BackendServer.objects(is_enabled=True,
                                         name__nin=[b.name for b in exclude]):
        if backend.run_plans:
            for run_plan in backend.run_plans:
                scores = dict(scores.items() +
                              {backend: run_plan.memory_limit}.items())
            log.debug(u"Backend %s has %d run plans, with final score %d" % (
                backend.name, len(backend.run_plans), scores[backend]))
        else:
            scores[backend] = 0
            log.debug(u"Backend %s has no run plans" % backend.name)
    if scores:
        log.debug(u"Backend scores: %s" % scores)
        score = sorted(scores.values())[0]
        for (backend, backend_score) in scores.items():
            if score == backend_score:
                return backend
    else:
        # no run plans, just return first backend
        return BackendServer.objects(
            is_enabled=True, name__nin=[b.name for b in exclude]).first()
