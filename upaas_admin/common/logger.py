# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
from datetime import datetime, timedelta


from upaas_admin.apps.tasks.models import TaskMessage


class MongoLogHandler(logging.StreamHandler):

    def __init__(self, task, flush_count=10, flush_time=3, *args,
                 **kwargs):
        super(MongoLogHandler, self).__init__(*args, **kwargs)

        self.task = task
        self.flush_count = flush_count
        self.flush_time = flush_time

        self.messages = []
        self.last_flush = datetime.now()

    def flush(self):
        self.task.__class__.objects(id=self.task.id).update_one(
            push_all__messages=self.messages)
        self.messages = []
        self.last_flush = datetime.now()

    def emit(self, record):
        msg = TaskMessage(timestamp=datetime.fromtimestamp(record.created),
                          source=record.name, level=record.levelno,
                          message=record.msg)
        self.messages.append(msg)
        if len(self.messages) >= self.flush_count:
            self.flush()
        elif datetime.now() - self.last_flush >= timedelta(
                seconds=self.flush_time):
            self.flush()
