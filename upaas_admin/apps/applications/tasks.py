# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging


log = logging.getLogger(__name__)


'''
@register
class StartApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Starting {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):

        if not self.application.run_plan:
            log.error("Missing run plan, cannot start "
                      "'%s'" % self.application.name)
            raise Exception("Missing run plan for "
                            "'%s'" % self.application.name)

        run_plan = self.application.run_plan

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            if backend_conf.package.id != self.application.current_package.id:
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
            log.info("Starting application '%s' using package '%s'" % (
                self.application.name, backend_conf.package.safe_id))

            if not os.path.exists(backend_conf.package.package_path):
                try:
                    backend_conf.package.unpack()
                except UnpackError as e:
                    log.error("Unpacking failed: %s" % e)
                    raise Exception("Unpacking package failed: %s" % e)
            else:
                log.warning("Package already exists: "
                            "%s" % backend_conf.package.package_path)
            yield 50

            backend_conf.package.save_vassal_config(backend_conf)
            # TODO handle backend start task failure with rescue code

            self.wait_until_running()
            yield 100
        else:
            log.error(_("Backend {backend} missing in run plan for "
                        "{name}").format(backend=self.backend.name,
                                         name=self.application.name))
            yield 100


@register
class StopApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Stopping {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        if os.path.isfile(self.application.vassal_path):
            log.info("Removing vassal config file "
                     "'%s'" % self.application.vassal_path)
            try:
                os.remove(self.application.vassal_path)
            except OSError as e:
                log.error("Can't remove vassal config file at '%s': %s" % (
                    self.application.vassal_path, e))
                raise
        else:
            log.warning("Vassal config file for application '%s' not found "
                        "at '%s" % (self.application.safe_id,
                                    self.application.vassal_path))
        yield 10

        self.wait_until_stopped()
        yield 75

        run_plan = self.application.run_plan
        if run_plan:
            run_plan.remove_backend_settings(self.backend)
        else:
            log.warning(_("Missing run plan for {name}, already "
                          "stopped?").format(name=self.application.name))

        self.application.remove_unpacked_packages()
        log.info("Application '%s' stopped" % self.application.name)
        yield 100

    def cleanup(self):
        run_plan = self.application.run_plan
        if run_plan and not run_plan.backends:
            log.info("Removing '%s' run plan" % self.application.name)
            run_plan.delete()


@register
class UpgradeApplicationTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Upgrading {name} on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        run_plan = self.application.run_plan
        if not run_plan:
            msg = str(_("Missing run plan for {name}, cannot "
                        "upgrade").format(name=self.application.name))
            log.warning(msg)
            raise Exception(msg)

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            if backend_conf.package.id != self.application.current_package.id:
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
            try:
                backend_conf.package.unpack()
            except UnpackError:
                log.error("Unpacking failed")
                raise
            yield 40

            backend_conf.package.save_vassal_config(backend_conf)
            yield 75

            self.wait_until_running()
            yield 95

            self.application.remove_unpacked_packages(
                exclude=[backend_conf.package.id])
            yield 100
        else:
            log.warning(_("No run plan for {name}, it was probably "
                          "stopped").format(name=self.application.name))
            yield 100


@register
class UpdateVassalTask(ApplicationBackendTask):

    def generate_title(self):
        return _("Updating {name} configuration on {backend}").format(
            name=self.application.name, backend=self.backend.name)

    def job(self):
        run_plan = self.application.run_plan
        if not run_plan:
            msg = str(_("Missing run plan for {name}, application was "
                        "already stopped?").format(
                name=self.application.name))
            log.warning(msg)
            yield 100
            raise StopIteration

        backend_conf = self.application.run_plan.backend_settings(self.backend)
        if backend_conf:

            if backend_conf.package.id != self.application.current_package.id:
                log.info(_("Old package on backend, running upgrade"))
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=self.application.current_package.id)
                try:
                    backend_conf.package.unpack()
                except UnpackError:
                    log.error("Unpacking failed")
                    raise
                yield 40

            backend_conf.package.save_vassal_config(backend_conf)
            yield 50

            self.wait_until_running()
            yield 95

            self.application.remove_unpacked_packages(
                exclude=[backend_conf.package.id])
            yield 100
        else:
            log.warning(_("No run plan for {name}, it was probably "
                          "stopped").format(name=self.application.name))
            yield 100


    def wait_until_running(self, timelimit=None):
        if timelimit is None:
            timelimit = self.graceful_timeout

        run_plan = self.backend.application_settings(self.application)
        if not run_plan:
            return False

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            ip = str(self.backend.ip)
            name = self.application.name
            # FIXME track pid change instead of initial sleep (?)
            sleep(3)
            timeout = datetime.now() + timedelta(seconds=timelimit)
            logged = False
            while datetime.now() <= timeout:
                s = fetch_json_stats(ip, backend_conf.stats)
                if s:
                    return True
                if logged:
                    log.debug(_("Waiting for {name} to start").format(
                        name=name))
                else:
                    log.info(_("Waiting for {name} to start").format(
                        name=name))
                    logged = True
                sleep(2)
            else:
                log.error(_("Timeout reached but {name} doesn't appear to be "
                            "running yet").format(name=name))

        return False

    def wait_until_stopped(self, timelimit=None):
        if timelimit is None:
            timelimit = self.graceful_timeout

        run_plan = self.backend.application_settings(self.application)
        if not run_plan:
            return False

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            ip = str(self.backend.ip)
            name = self.application.name
            # FIXME track pid change instead of initial sleep (?)
            sleep(3)
            timeout = datetime.now() + timedelta(seconds=timelimit)
            logged = False
            while datetime.now() <= timeout:
                s = fetch_json_stats(ip, backend_conf.stats)
                if not s:
                    return True
                if logged:
                    log.debug(_("Waiting for {name} to stop").format(
                        name=name))
                else:
                    log.info(_("Waiting for {name} to stop").format(
                        name=name))
                    logged = True
                sleep(2)
            else:
                log.error(_("Timeout reached but {name} doesn't appear to be "
                            "stopped yet").format(name=name))

        return False
'''
