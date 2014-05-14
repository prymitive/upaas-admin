# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from operator import itemgetter

import logging

from django.utils.translation import ugettext as _
from django.conf import settings

from upaas_admin.apps.servers.models import BackendServer
from upaas_admin.apps.scheduler.models import BackendRunPlanSettings


log = logging.getLogger(__name__)


class Scheduler(object):

    def __init__(self):
        self.backends = BackendServer.objects(is_enabled=True)
        self.backend_by_id = dict((b.safe_id, b) for b in self.backends)
        self.backends_count = len(self.backends)
        self.default_worker_memory = \
            settings.UPAAS_CONFIG.defaults.limits.memory_per_worker
        self.allocated_mem = {}
        self.allocated_cpu = {}
        self.mem_load = {}
        self.cpu_load = {}
        self.scores = {}
        self.calculate_scores()

    def calculate_scores(self):
        self.allocated_mem = {}
        self.allocated_cpu = {}
        self.mem_load = {}
        self.cpu_load = {}
        self.scores = {}

        for backend in self.backends:
            self.allocated_mem[backend.safe_id] = 0
            self.allocated_cpu[backend.safe_id] = 0
            for run_plan in backend.run_plans:
                bconf = run_plan.backend_settings(backend)
                self.allocated_mem[backend.safe_id] += \
                    bconf.workers_max * run_plan.memory_per_worker
                self.allocated_cpu[backend.safe_id] += bconf.workers_max

        for backend in self.backends:
            self.update_load(backend.safe_id)
            self.update_score(backend.safe_id)
            log.debug(_(
                "Backend {name} current allocations: cpu={cpu} memory={mem}, "
                "load: cpu={cpuload} mem={memload}, score={score}").format(
                    name=backend.name,
                    cpu=self.allocated_cpu[backend.safe_id],
                    mem=self.allocated_mem[backend.safe_id],
                    cpuload=self.cpu_load[backend.safe_id],
                    memload=self.mem_load[backend.safe_id],
                    score=self.scores[backend.safe_id]))

    def update_load(self, backend_id):
        backend = self.backend_by_id[backend_id]
        mem_load = self.allocated_mem[backend_id] / float(backend.memory_mb)
        cpu_load = self.allocated_cpu[backend_id] / float(backend.cpu_cores)
        self.mem_load[backend_id] = mem_load
        self.cpu_load[backend_id] = cpu_load

    def update_score(self, backend_id):
        backend = self.backend_by_id[backend_id]
        mem_free = backend.memory_mb - self.allocated_mem[backend_id]
        cpu_load = self.mem_load[backend_id]
        mem_load = self.mem_load[backend_id]
        self.scores[backend_id] = cpu_load * mem_load
        if mem_load > 0.9 or mem_free <= self.default_worker_memory:
            # backend is overloaded put it on the bottom of the list
            self.scores[backend.safe_id] *= 99999

    def backends_range(self, max_workers):
        """
        Returns number of backends that should be used for given number of
        workers. Tuple is returned (min backend count, max backend count).
        """
        if max_workers == 1:
            return 1, 1
        elif max_workers <= 4:
            return min(2, self.backends_count), min(2, self.backends_count)
        elif max_workers <= 8:
            return min(2, self.backends_count), min(2, self.backends_count)
        elif max_workers <= 15:
            return min(3, self.backends_count), min(3, self.backends_count)
        elif max_workers <= 32:
            return min(4, self.backends_count), min(8, self.backends_count)
        else:
            return min(5, self.backends_count), max(5, self.backends_count)

    def select_best_backend(self, plan, min_backends, max_backends):
        """
        Select least loaded backend for application run plan.
        Backend ID is returned (string format).
        """
        for bid, __ in sorted(self.scores.items(), key=itemgetter(1, 0)):
            if bid in plan and len(plan.keys()) < min_backends:
                # backend is already scheduled and we need more backends
                # skip it so we can fulfill min_backends requirement
                continue
            elif bid not in plan and len(plan.keys()) >= max_backends:
                # backend is not scheduled but we already got maximum backends
                # retured, skip it so we can fulfill max_backends requirement
                continue
            return bid

    def find_backends(self, run_plan):
        plan_max = {}
        plan_min = {}
        min_backends, max_backends = self.backends_range(run_plan.workers_max)
        log.info(_("Will use between {minb} and {maxb} backends").format(
            minb=min_backends, maxb=max_backends))

        scheduled_max = 0
        while scheduled_max < run_plan.workers_max:
            bid = self.select_best_backend(plan_max, min_backends,
                                           max_backends)
            if bid is None:
                log.error(_("No more backends can be found, got only "
                            "{l}").format(l=len(plan_max.keys())))
                if plan_max:
                    break
                else:
                    return []
            plan_max[bid] = plan_max.get(bid, 0) + 1
            # allocations must to updated only for max workers
            self.allocated_cpu[bid] += 1
            self.allocated_mem[bid] += run_plan.memory_per_worker
            self.update_load(bid)
            self.update_score(bid)
            scheduled_max += 1

        scheduled_min = 0
        for bid, workers_max in plan_max.items():
            if run_plan.workers_min == run_plan.workers_max:
                plan_min[bid] = plan_max[bid]
            else:
                plan_min[bid] = 1
            scheduled_min += plan_min[bid]

        log.debug(_("Scheduled min workers: {m}, needed {n}").format(
            m=scheduled_min, n=run_plan.workers_min))

        missing = run_plan.workers_min - scheduled_min
        log.debug(_("Missing min workers: {m}").format(m=missing))
        while missing > 0:
            log.debug(_("Still missing min workers: {m}").format(m=missing))
            for bid, __ in sorted(self.scores.items(), key=itemgetter(1)):
                if bid in plan_max and plan_max[bid] > plan_min[bid]:
                    backend = self.backend_by_id[bid]
                    log.debug(_("Adding missing min worker to {name}").format(
                        name=backend.name))
                    plan_min[bid] += 1
                    missing -= 1
                    if missing <= 0:
                        break

        backends = []

        for bid, workers_max in sorted(plan_max.items(), key=itemgetter(1, 0)):
            workers_min = plan_min[bid]
            backend = self.backend_by_id[bid]
            backend_conf = run_plan.backend_settings(backend)
            values = {}
            if backend_conf:
                values['socket'] = backend_conf.socket
                values['stats'] = backend_conf.stats
            else:
                ports = backend.find_free_ports(2)
                values['socket'] = ports[0]
                values['stats'] = ports[1]
                if not ports:
                    log.error(_("No free ports found on backend "
                                "{name}").format(name=backend.name))
                    continue
            brps = BackendRunPlanSettings(
                backend=backend,
                workers_min=workers_min,
                workers_max=workers_max,
                package=run_plan.application.current_package,
                **values)
            backends.append(brps)

        log.info(_("Got backends for {name}: {servers}").format(
            name=run_plan.application.name, servers=", ".join(
                ["%s: %d - %d" % (b.backend.name, b.workers_min,
                                  b.workers_max) for b in backends])))
        log.info(_("Total workers for {name}: {minw} - {maxw}").format(
            name=run_plan.application.name, minw=sum(plan_min.values()),
            maxw=sum(plan_max.values())))

        return backends
