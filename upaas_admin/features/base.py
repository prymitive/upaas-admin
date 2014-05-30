# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from upaas.config.base import Config, BooleanEntry


class Feature(object):

    # default set of options for every feature
    base_configuration_schema = {
        'enabled': BooleanEntry()
    }

    # feature specific options
    configuration_schema = {}

    def __init__(self, settings):
        schema = self.configuration_schema
        schema.update(self.base_configuration_schema)
        self.settings = Config(settings, schema=schema)

    def update_vassal(self, options):
        """
        Called at the end of uWSGI vassal config file generation, can be used
        to add new or alter already stored options.
        """
        # FIXME add to code
        return options

    def builder_mule_update_env(self, env):
        """
        Called every time a command is going to be executed in builder mule,
        it can be used to update environment variables.
        """
        # FIXME add to code
        return env

    def builder_mule_after_clone(self):
        """
        Called in builder mule after cloning application repository.
        """
        # FIXME add to code
        pass

    def backend_mule_after_unpack(self):
        """
        Called in backend mule after application package is unpacked.
        """
        # FIXME add to code
        pass
