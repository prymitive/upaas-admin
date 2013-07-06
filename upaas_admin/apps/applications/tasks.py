# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import absolute_import

from celery import current_task
from celery.utils.log import get_task_logger
from celery.exceptions import Ignore
from celery.states import FAILURE

from upaas.config.base import ConfigurationError
from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions

from upaas_tasks.celery import celery


log = get_task_logger(__name__)


@celery.task
def build_package(metadata, force_fresh=False):
    try:
        metadata_obj = MetadataConfig.from_string(metadata)
    except ConfigurationError:
        log.error(u"Invalid app metadata")
        build_package.update_state(state=FAILURE)
        raise Ignore()

    builder_config = load_main_config()
    if not builder_config:
        log.error(u"Missing uPaaS configuration")
        build_package.update_state(state=FAILURE)
        raise Ignore()

    builder = Builder(builder_config, metadata_obj)
    build_result = None
    try:
        for result in builder.build_package(force_fresh=force_fresh):
            log.info("Build progress: %d%%" % result.progress)
            current_task.update_state(state='PROGRESS',
                                      meta={'current': result.progress,
                                            'total': 100})
            build_result = result
    except exceptions.BuildError:
        log.error(u"Build failed")
        build_package.update_state(state=FAILURE)
        raise Ignore()
    else:
        log.info(u"Build completed")
        return build_result
