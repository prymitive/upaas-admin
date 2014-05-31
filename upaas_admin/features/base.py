# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.config.base import Config


class Feature(object):

    # feature specific options
    configuration_schema = {}

    def __init__(self, name, settings):
        self.name = name
        self.settings = Config(settings, schema=self.configuration_schema)

    def update_vassal(self, application, options):
        """
        Called at the end of uWSGI vassal config file generation, can be used
        to add new or alter already stored options.
        """
        return options

    def after_unpack(self, application, workdir):
        """
        Called after application package is unpacked.
        """
        pass

    def builder_mule_update_env(self, application, env):
        """
        Called every time a command is going to be executed in builder mule,
        it can be used to update environment variables.
        """
        # FIXME add to code
        return env

    def builder_mule_after_clone(self, application):
        """
        Called in builder mule after cloning application repository.
        """
        # FIXME add to code
        pass
