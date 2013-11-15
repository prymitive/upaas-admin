# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from upaas_admin.apps.servers.models import BackendServer


log = logging.getLogger(__name__)


def select_best_backend(exclude=None, application=None):
    """
    Return backend server that is the least loaded one or None if there is no
    enabled backend.
    """
    if exclude is None:
        exclude = []
    #FIXME make it aware of each backend resources
    scores = {}
    for backend in BackendServer.objects(is_enabled=True,
                                         id__nin=[b.id for b in exclude]):
        if backend.run_plans:
            for run_plan in backend.run_plans:
                if application and run_plan.application.id == application.id:
                    # if this run plan is for application we are trying to find
                    # backends than ignore it, prevents jumping apps on update
                    continue
                scores = dict(scores.items() +
                              {backend: run_plan.memory_limit}.items())
            log.debug(u"Backend %s has %d run plans, with final score %d" % (
                backend.name, len(backend.run_plans), scores.get(backend, 0)))
        else:
            scores[backend] = 0
            log.debug(u"Backend %s has no run plans" % backend.name)
    if sum(scores.values()):
        log.debug(u"Backend scores: %s" % scores)
        score = sorted(scores.values())[0]
        for (backend, backend_score) in scores.items():
            if score == backend_score:
                return backend
    else:
        # no run plans, just return first backend
        return BackendServer.objects(
            is_enabled=True, id__nin=[b.id for b in exclude]).first()


def select_best_backends(run_plan):
    """
    Select best backends for given application run plan. Returns a list of
    backends where application should be running. If there are no backends to
    run empty list will be returned.
    """
    #TODO needs better scheduling of the number of backends application should
    # use

    log.info(u"Selecting backends for %s, ha: %s" % (
        run_plan.application.name, run_plan.ha_enabled))

    available_backends = len(BackendServer.objects(is_enabled=True))
    if available_backends == 0:
        return []

    if run_plan.ha_enabled:
        num_backends = min(2, available_backends)
    else:
        num_backends = 1

    backends = []
    for i in xrange(0, num_backends):
        backend = select_best_backend(exclude=backends,
                                      application=run_plan.application)
        if backend:
            backends.append(backend)
        else:
            log.warning(u"Can find more available backends, got %d, needed "
                        u"%d" % (i+1, num_backends))
            break

    log.info(u"Got backends for %s: %s" % (run_plan.application.name,
                                           [b.name for b in backends]))

    return backends
