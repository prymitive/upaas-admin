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

from mongoengine import Document, ReferenceField, StringField, QuerySetManager

from pymongo import Connection

from upaas.config.base import StringEntry

from upaas_admin.features.base import Feature


log = logging.getLogger(__name__)


class FeatureApplicationMongodbAuth(Document):

    application = ReferenceField('Application', required=True)
    login = StringField(required=True)
    password = StringField(required=True)

    meta = {
        'indexes': ['application'],
    }

    _default_manager = QuerySetManager()


class MongoDBFeature(Feature):

    configuration_schema = {
        "uri": StringEntry(required=True),
        "template": StringEntry(required=True),
    }

    env_key = 'UPAAS_MONGODB_URI'

    def generate_name(self, application):
        return '%s-%s' % (application.name, application.safe_id)

    def generate_uri(self, application):
        name = self.generate_name(application)
        login, password = self.generate_auth(application)
        return self.settings.template.replace("%database%", name).replace(
            "%login%", login).replace("%password%", password)

    def generate_auth(self, application):
        auth = FeatureApplicationMongodbAuth.objects(
            application=application).first()
        if not auth:
            auth = FeatureApplicationMongodbAuth(
                application=application,
                login=self.generate_name(application),
                password=hmac.new(uuid.uuid4().bytes,
                                  digestmod=hashlib.sha1).hexdigest())
            auth.save()
        return auth.login, auth.password

    def update_env(self, application, env):
        env[self.env_key] = self.generate_uri(application)
        return env

    def before_building(self, application):
        name = self.generate_name(application)
        login, password = self.generate_auth(application)
        connection = Connection(self.settings.uri)
        if name not in connection.database_names():
            log.info(_("Creating MongoDB database: {name}").format(name=name))
            db = connection[name]
            collection_name = 'upaas_test'
            collection = db[collection_name]
            collection.insert({})
            db.drop_collection(collection_name)
            db.add_user(login, password, roles=['dbAdmin'])
            db.authenticate(login, password)
            db.logout()
        connection.close()
