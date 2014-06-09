# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging
import hmac
import uuid
import hashlib

from django.utils.translation import ugettext as _

from mongoengine import (Document, ReferenceField, StringField, IntField,
                         QuerySetManager)

from psycopg2 import connect, OperationalError

from upaas.config.base import StringEntry

from upaas_admin.features.base import Feature


log = logging.getLogger(__name__)


class FeatureApplicationPostgresqlAuth(Document):

    application = ReferenceField('Application', required=True)
    login = StringField(required=True)
    password = StringField(required=True)

    meta = {
        'indexes': ['application'],
    }

    _default_manager = QuerySetManager()


class PostgreSQLFeature(Feature):

    configuration_schema = {
        "host": StringEntry(required=True),
        "port": IntField(min_value=1, max_value=65535, default=5432,
                         required=True),
        "login": StringEntry(required=True),
        "password": StringEntry(),
    }

    env_key_host = 'PGHOST'
    env_key_port = 'PGPORT'
    env_key_db = 'PGDATABASE'
    env_key_login = 'PGUSER'
    env_key_password = 'PGPASSWORD'

    def generate_name(self, application):
        return '%s-%s' % (application.name, application.safe_id)

    def generate_auth(self, application):
        auth = FeatureApplicationPostgresqlAuth.objects(
            application=application).first()
        if not auth:
            auth = FeatureApplicationPostgresqlAuth(
                application=application,
                login=self.generate_name(application),
                password=hmac.new(uuid.uuid4().bytes,
                                  digestmod=hashlib.sha1).hexdigest())
            auth.save()
        return auth.login, auth.password

    def update_env(self, application, env):
        login, password = self.generate_auth(application)

        env[self.env_key_login] = login
        env[self.env_key_password] = password
        env[self.env_key_db] = self.generate_name(application)
        return env

    def before_building(self, application):
        name = self.generate_name(application)
        login, password = self.generate_auth(application)

        try:
            connection = connect(dbname='postgres', host=self.settings.host,
                                 port=self.settings.port, user=login,
                                 password=password)
        except OperationalError:
            log.info(_("Creating PostgreSQL database: "
                       "{name}").format(name=name))
            connection = connect(dbname='postgres', host=self.settings.host,
                                 port=self.settings.port,
                                 user=self.settings.login,
                                 password=self.settings.password or None)
            cursor = connection.cursor()
            cursor.execute("CREATE USER %s WITH PASSWORD '%s'",
                           (login, password))
            cursor.execute("CREATE DATABASE %s" % name)
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE %s to %s",
                           (name, login))
            cursor.close()
            connection.close()
        else:
            connection.close()
