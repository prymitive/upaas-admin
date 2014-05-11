# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.scheduler.base import Scheduler


class SchedulerTest(MongoEngineTestCase):

    def create_run_plan(self, min_workers, max_workers):
        return ApplicationRunPlan(application=self.app,
                                  workers_min=min_workers,
                                  workers_max=max_workers,
                                  memory_per_worker=128,
                                  max_log_size=1)

    def backends_count_check(self, min_workers, max_workers, expected):
        run_plan = self.create_run_plan(min_workers, max_workers)
        scheduler = Scheduler()
        backends = scheduler.find_backends(run_plan)
        self.assertEqual(len(backends), len(expected))

        total_min = 0
        total_max = 0
        bconfs = []
        for bconf in backends:
            bconfs.append((bconf.workers_min, bconf.workers_max))
            total_min += bconf.workers_min
            total_max += bconf.workers_max
        bconfs = sorted(bconfs)

        self.assertEqual(total_max, max_workers)
        self.assertTrue(min_workers <= total_min <= max_workers)

        expected = sorted(expected)

        idx = 0
        for bmin, bmax in bconfs:
            self.assertEqual(bmin, expected[idx][0])
            self.assertEqual(bmax, expected[idx][1])
            idx += 1

    @pytest.mark.usefixtures("create_app", "create_pkg")
    def test_scheduler_no_backends(self):
        run_plan = self.create_run_plan(1, 1)
        scheduler = Scheduler()
        backends = scheduler.find_backends(run_plan)
        self.assertEqual(len(backends), 0)

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_backend_list")
    def test_scheduler_select_best_backends(self):
        self.backends_count_check(1, 1, [(1, 1)])
        self.backends_count_check(1, 4, [(1, 2), (1, 2)])
        self.backends_count_check(3, 8, [(1, 4), (2, 4)])
        self.backends_count_check(4, 5, [(2, 3), (2, 2)])
        self.backends_count_check(2, 8, [(1, 4), (1, 4)])
        self.backends_count_check(4, 8, [(2, 4), (2, 4)])
        self.backends_count_check(9, 11, [(3, 3), (3, 4), (3, 4)])
        self.backends_count_check(10, 10, [(3, 3), (4, 4), (3, 3)])

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_backend_list")
    def test_scheduler_select_best_backends_huge(self):
        self.backends_count_check(1, 40, [(1, 4) for _ in range(0, 10)])
        self.backends_count_check(500, 1000, [(50, 100) for _ in range(0, 10)])
