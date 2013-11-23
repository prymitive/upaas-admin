# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from django.utils.translation import ugettext_lazy as _

from upaas_admin.apps.servers.models import BackendServer
from upaas_admin.apps.scheduler.models import BackendRunPlanSettings


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
                scores = dict(scores.items() + {
                    backend: run_plan.workers_max * run_plan.memory_per_worker
                }.items())
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


def split_workers(workers, backends):
    #TODO right now we try to split workers into equal chunks, but we need
    # to do this with each backend resources in mind
    workers_list = range(workers)
    return [len(workers_list[i::backends]) for i in xrange(backends)]


def select_best_backends(run_plan):
    """
    Select best backends for given application run plan. Returns a list of
    backends where application should be running. If there are no backends to
    run empty list will be returned.
    """
    #TODO needs better scheduling of the number of backends application should
    # use

    #FIXME translate
    log.info(u"Selecting backends for %s, workers: %d - %d, memory per "
             u"worker: %d MB" % (run_plan.application.name,
                                 run_plan.workers_min, run_plan.workers_max,
                                 run_plan.memory_per_worker))

    available_backends = len(BackendServer.objects(is_enabled=True))
    if available_backends == 0:
        return []

    #FIXME support workers_min

    if available_backends == 1:
        needs_backends = 1
    elif run_plan.workers_min < 4:
        needs_backends = 1
    elif run_plan.workers_min < 9:
        needs_backends = 2
    else:
        needs_backends = run_plan.workers_max / 3
    if needs_backends > available_backends:
        needs_backends = available_backends

    workers_per_backend = split_workers(run_plan.workers_max, needs_backends)
    log.info(_(u"Worker mapping for {name}: {count} backends, "
               u"{mapping}").format(name=run_plan.application.name,
                                    count=needs_backends,
                                    mapping=workers_per_backend))

    backends = []
    for workers_count in workers_per_backend:
        backend = select_best_backend(exclude=[b.backend for b in backends],
                                      application=run_plan.application)
        if backend:
            ports = backend.find_free_ports(2)
            if not ports:
                log.warning(_(u"Didn't found free ports on backend "
                              u"{name}").format(name=backend.name))
                continue
            #FIXME use proper workers_min
            brps = BackendRunPlanSettings(backend=backend, socket=ports[0],
                                          stats=ports[1],
                                          workers_min=1,
                                          workers_max=workers_count)
            backends.append(brps)
        else:
            log.warning(_(u"Can find more available backends, got {got}, "
                          u"{needed}").format(got=len(backends),
                                              needed=needs_backends))
            break

    log.info(_(u"Got backends for {name}: {servers}").format(
        name=run_plan.application.name,
        servers=u", ".join([u"%s: %d - %d" % (
            b.backend.name, b.workers_min, b.workers_max) for b in backends])))

    return backends
