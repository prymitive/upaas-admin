# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from django.core.management import call_command

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.scheduler.models import (BackendRunPlanSettings,
                                               ApplicationRunPlan)


class RunPlanMigrationTest(MongoEngineTestCase):

    @pytest.mark.usefixtures("create_pkg", "create_backend", "create_router")
    def test_run_plan_migration(self):

        backend_settings = BackendRunPlanSettings(backend=self.backend,
                                                  package=self.pkg,
                                                  socket=8080, stats=9090,
                                                  workers_min=1, workers_max=4)

        run_plan = ApplicationRunPlan(application=self.app,
                                      backends=[backend_settings],
                                      workers_min=1, workers_max=4,
                                      memory_per_worker=128, max_log_size=1)
        run_plan.save()

        self.app.reload()
        self.assertEqual(self.app.run_plan, None)
        self.assertEqual(call_command('migrate_db'), None)
        self.app.reload()
        self.assertEqual(self.app.run_plan, run_plan)

        run_plan.delete()
