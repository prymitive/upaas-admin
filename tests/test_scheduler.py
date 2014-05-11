# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.scheduler.base import select_best_backends


class SchedulerTest(MongoEngineTestCase):

    def create_run_plan(self, min_workers, max_workers):
        return ApplicationRunPlan(application=self.app,
                                  workers_min=min_workers,
                                  workers_max=max_workers,
                                  memory_per_worker=128,
                                  max_log_size=1)

    def backends_count_check(self, min_workers, max_workers, expected):
        run_plan = self.create_run_plan(min_workers, max_workers)
        backends = select_best_backends(run_plan)
        self.assertEqual(len(backends), len(expected))

        idx = 0
        for bconf in backends:
            emin, emax = expected[idx]
            self.assertEqual(bconf.workers_min, emin)
            self.assertEqual(bconf.workers_max, emax)
            idx += 1

    @pytest.mark.usefixtures("create_app", "create_pkg")
    def test_scheduler_no_backends(self):
        run_plan = self.create_run_plan(1, 1)
        backends = select_best_backends(run_plan)
        self.assertEqual(len(backends), 0)

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_backend_list")
    def test_scheduler_select_best_backends(self):
        return
        self.backends_count_check(1, 1, [(1, 1)])
        self.backends_count_check(1, 4, [(1, 4)])
        self.backends_count_check(4, 5, [(2, 3), (2, 2)])
        self.backends_count_check(2, 8, [(1, 4), (1, 4)])
        self.backends_count_check(4, 8, [(2, 4), (2, 4)])
        self.backends_count_check(10, 10, [(5, 5), (5, 5)])
