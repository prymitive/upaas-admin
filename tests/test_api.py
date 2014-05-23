# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from tastypie.test import ResourceTestCase

from django.core.management import call_command

from upaas_admin.common.tests import MongoEngineTestCase
from upaas_admin.apps.applications.models import Package
from upaas_admin.apps.applications.constants import NeedsBuildingFlag


class ApiTest(MongoEngineTestCase, ResourceTestCase):

    def get_apikey_auth(self, user):
        return {'HTTP_X_UPAAS_LOGIN': user.username,
                'HTTP_X_UPAAS_APIKEY': user.apikey}

    @pytest.mark.usefixtures("create_user")
    def test_auth_invalid_apikey(self):
        self.user.apikey = '1234567890'
        self.assertHttpUnauthorized(self.api_client.get(
            '/api/v1/application/', format='json',
            **self.get_apikey_auth(self.user)))

    def test_applications_auth(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/application/',
                                                        format='json'))

    def test_backend_auth(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/backend/',
                                                        format='json'))

    def test_packages_auth(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/package/',
                                                        format='json'))

    def test_router_auth(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/router/',
                                                        format='json'))

    def test_run_plan_auth(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/run_plan/',
                                                        format='json'))

    def test_tasks_auth(self):
        self.assertHttpUnauthorized(self.api_client.get('/api/v1/task/',
                                                        format='json'))

    @pytest.mark.usefixtures("create_app")
    def test_application_list_get(self):
        resp = self.api_client.get('/api/v1/application/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    @pytest.mark.usefixtures("create_pkg")
    def test_application_detail_get(self):
        resp = self.api_client.get(
            '/api/v1/application/%s/' % self.app.safe_id, format='json',
            **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['name'], self.app.name)
        self.assertEqual(self.deserialize(resp)['owner'], self.user.username)
        self.assertEqual(self.deserialize(resp)['current_package']['id'],
                         self.pkg.safe_id)
        self.assertKeys(self.deserialize(resp),
                        ['can_start', 'current_package', 'date_created', 'id',
                         'instance_count', 'metadata', 'name', 'owner',
                         'resource_uri', 'run_plan', 'running_tasks'])

    @pytest.mark.usefixtures("create_user")
    def test_application_detail_get_404(self):
        self.assertHttpNotFound(self.api_client.get(
            '/api/v1/application/535cd85d5ba72e0e61181382/', format='json',
            **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_user")
    def test_application_detail_get_404_invalid(self):
        self.assertHttpNotFound(self.api_client.get(
            '/api/v1/application/1234/', format='json',
            **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_user")
    def test_application_list_empty_get(self):
        resp = self.api_client.get('/api/v1/application/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    @pytest.mark.usefixtures("create_app")
    def test_application_post(self):
        post_data = {'name': 'testapp1', 'metadata': self.app_data['metadata']}
        self.assertHttpCreated(
            self.api_client.post('/api/v1/application/', format='json',
                                 data=post_data,
                                 **self.get_apikey_auth(self.user)))

        resp = self.api_client.get('/api/v1/application/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        resp = self.api_client.get('/api/v1/application/?name=testapp1',
                                   format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['name'],
                         'testapp1')
        self.assertEqual(self.deserialize(resp)['objects'][0]['metadata'],
                         self.app_data['metadata'])

    @pytest.mark.usefixtures("create_app")
    def test_application_patch_metadata(self):
        metadata = self.app_data['metadata'] + '\n\n#updated'
        app_url = '/api/v1/application/%s/' % self.app.safe_id
        self.assertHttpAccepted(self.api_client.patch(
            app_url, format='json', data={'metadata': metadata},
            **self.get_apikey_auth(self.user)))

        resp = self.api_client.get(app_url, format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['name'], self.app.name)
        self.assertEqual(self.deserialize(resp)['metadata'], metadata)

    @pytest.mark.usefixtures("create_app")
    def test_application_patch_name(self):
        name = 'newappname'
        app_url = '/api/v1/application/%s/' % self.app.safe_id
        self.assertHttpAccepted(self.api_client.patch(
            app_url, format='json', data={'name': name},
            **self.get_apikey_auth(self.user)))

        resp = self.api_client.get(app_url, format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['name'], self.app.name)
        self.assertEqual(self.deserialize(resp)['metadata'],
                         self.app_data['metadata'])

    @pytest.mark.usefixtures("create_user")
    def test_application_invalid_metadata_post(self):
        post_data = {'name': 'testapp1', 'metadata': '12345'}
        self.assertHttpBadRequest(
            self.api_client.post('/api/v1/application/', format='json',
                                 data=post_data,
                                 **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_user")
    def test_application_missing_metadata_post(self):
        post_data = {'name': 'testapp1'}
        self.assertHttpBadRequest(
            self.api_client.post('/api/v1/application/', format='json',
                                 data=post_data,
                                 **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_app")
    def test_application_invalid_name_post(self):
        post_data = {'name': 'a', 'metadata': self.app_data['metadata']}
        self.assertHttpBadRequest(
            self.api_client.post('/api/v1/application/', format='json',
                                 data=post_data,
                                 **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_app")
    def test_application_duplicated_name_post(self):
        post_data = {'name': self.app_data['name'],
                     'metadata': self.app_data['metadata']}
        self.assertHttpBadRequest(
            self.api_client.post('/api/v1/application/', format='json',
                                 data=post_data,
                                 **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_app")
    def test_application_delete_single(self):
        app_url = '/api/v1/application/%s/' % self.app.safe_id
        self.assertHttpUnauthorized(self.api_client.delete(
            app_url, format='json', **self.get_apikey_auth(self.user)))

        resp = self.api_client.get(app_url, format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['name'], self.app.name)
        self.assertEqual(self.deserialize(resp)['metadata'],
                         self.app_data['metadata'])

    @pytest.mark.usefixtures("create_app")
    def test_application_delete_all(self):
        self.assertHttpUnauthorized(self.api_client.delete(
            '/api/v1/application/', format='json',
            **self.get_apikey_auth(self.user)))

        resp = self.api_client.get('/api/v1/application/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    @pytest.mark.usefixtures("create_app")
    def test_application_build_package(self):
        self.assertHttpCreated(self.api_client.put(
            '/api/v1/application/%s/build/' % self.app.safe_id, format='json',
            **self.get_apikey_auth(self.user)))
        flag = self.app.flags.first()
        self.assertNotEqual(flag, None)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_fresh_package], False)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_interpreter_version],
            None)

    @pytest.mark.usefixtures("create_app")
    def test_application_build_package_404(self):
        self.assertHttpNotFound(self.api_client.put(
            '/api/v1/application/12345/build/', format='json',
            **self.get_apikey_auth(self.user)))
        flag = self.app.flags.first()
        self.assertEqual(flag, None)

    @pytest.mark.usefixtures("create_app")
    def test_application_build_package_force_fresh(self):
        self.assertHttpCreated(self.api_client.put(
            '/api/v1/application/%s/build/?force_fresh=1' % self.app.safe_id,
            format='json', **self.get_apikey_auth(self.user)))
        flag = self.app.flags.first()
        self.assertNotEqual(flag, None)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_fresh_package], True)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_interpreter_version],
            None)

    @pytest.mark.usefixtures("create_app")
    def test_application_build_package_force_fresh_invalid(self):
        self.assertHttpCreated(self.api_client.put(
            '/api/v1/application/%s/build/?force_fresh=a4x' % self.app.safe_id,
            format='json', **self.get_apikey_auth(self.user)))
        flag = self.app.flags.first()
        self.assertNotEqual(flag, None)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_fresh_package], False)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_interpreter_version],
            None)

    @pytest.mark.usefixtures("create_app")
    def test_application_build_package_interpreter_version(self):
        self.assertHttpCreated(self.api_client.put(
            '/api/v1/application/%s/build/?interpreter_version=1.9.3' % (
                self.app.safe_id),
            format='json', **self.get_apikey_auth(self.user)))
        flag = self.app.flags.first()
        self.assertNotEqual(flag, None)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_fresh_package], False)
        self.assertEqual(
            flag.options[NeedsBuildingFlag.Options.build_interpreter_version],
            '1.9.3')

    @pytest.mark.usefixtures("create_app")
    def test_application_build_package_interpreter_version_unsupported(self):
        self.assertHttpBadRequest(self.api_client.put(
            '/api/v1/application/%s/build/?interpreter_version=123' % (
                self.app.safe_id),
            format='json', **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_pkg_list")
    def test_package_list_get(self):
        resp = self.api_client.get('/api/v1/package/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 20)

        resp = self.api_client.get('/api/v1/package/', format='json',
                                   data={'offset': 20},
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 13)

    @pytest.mark.usefixtures("create_pkg_list")
    def test_package_list_limit_get(self):
        resp = self.api_client.get('/api/v1/package/', format='json',
                                   data={'limit': 40},
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 33)

    @pytest.mark.usefixtures("create_pkg")
    def test_package_detail_get(self):
        resp = self.api_client.get(
            '/api/v1/package/%s/' % self.pkg.safe_id, format='json',
            **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['builder'], 'fake builder')
        self.assertEqual(self.deserialize(resp)['bytes'], '1024')

    @pytest.mark.usefixtures("create_user")
    def test_package_detail_get_404(self):
        self.assertHttpNotFound(self.api_client.get(
            '/api/v1/package/535cd85d5ba72e0e61181382/', format='json',
            **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_user")
    def test_package_detail_get_404_invalid(self):
        self.assertHttpNotFound(self.api_client.get(
            '/api/v1/package/1234/', format='json',
            **self.get_apikey_auth(self.user)))

    @pytest.mark.usefixtures("create_pkg_list")
    def test_package_delete_single(self):
        pkg = self.pkg_list[15]
        pkg_url = '/api/v1/package/%s/' % pkg.safe_id
        self.assertHttpAccepted(self.api_client.delete(
            pkg_url, format='json', **self.get_apikey_auth(self.user)))

        self.assertHttpNotFound(self.api_client.get(
            pkg_url, format='json', **self.get_apikey_auth(self.user)))

        resp = self.api_client.get('/api/v1/package/', format='json',
                                   data={'limit': 40},
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 32)

        self.app.reload()
        self.assertEqual(len(self.app.packages), 32)

    @pytest.mark.usefixtures("create_pkg")
    def test_package_delete_single_current(self):
        pkg_url = '/api/v1/package/%s/' % self.pkg.safe_id
        self.assertHttpUnauthorized(self.api_client.delete(
            pkg_url, format='json', **self.get_apikey_auth(self.user)))

        resp = self.api_client.get(pkg_url, format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['bytes'], str(self.pkg.bytes))

    @pytest.mark.usefixtures("create_pkg_list")
    def test_package_delete_all(self):
        self.assertHttpAccepted(self.api_client.delete(
            '/api/v1/package/', format='json',
            **self.get_apikey_auth(self.user)))

        resp = self.api_client.get('/api/v1/package/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        resp = self.api_client.get(
            '/api/v1/package/%s/' % self.app.current_package.safe_id,
            format='json', **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['bytes'],
                         str(self.app.current_package.bytes))

    @pytest.mark.usefixtures("create_pkg_list", "create_user_list_with_apps")
    def test_package_delete_all_owned(self):
        packages = {}
        i = 10
        for user, app in self.user_list_apps.items():
            pkg = self.pkg_list[i]
            pkg.application = app
            pkg.save()
            packages[user] = pkg
            i += 1

        self.assertHttpAccepted(self.api_client.delete(
            '/api/v1/package/', format='json',
            **self.get_apikey_auth(self.user)))

        self.assertEqual(len(Package.objects()), 11)

        for user, pkg in packages.items():
            resp = self.api_client.get(
                '/api/v1/package/%s/' % pkg.safe_id, format='json',
                **self.get_apikey_auth(user))
            self.assertValidJSONResponse(resp)
            self.assertEqual(self.deserialize(resp)['builder'], 'fake builder')
            self.assertEqual(self.deserialize(resp)['bytes'], '1024')

        resp = self.api_client.get('/api/v1/package/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        resp = self.api_client.get(
            '/api/v1/package/%s/' % self.app.current_package.safe_id,
            format='json', **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['bytes'],
                         str(self.app.current_package.bytes))

    @pytest.mark.usefixtures("create_user")
    def test_task_list_empty_get(self):
        resp = self.api_client.get('/api/v1/task/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    @pytest.mark.usefixtures("create_app", "create_pkg", "create_run_plan")
    def test_task_details_get(self):
        self.app.start_application()
        call_command('mule_backend', task_limit=1, ping_disabled=True)
        task = self.app.tasks.first()

        resp = self.api_client.get('/api/v1/task/%s/' % task.safe_id,
                                   format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['title'],
                         'Starting application instance')
        self.assertEqual(self.deserialize(resp)['flag'], 'IS_STARTING')
        self.assertEqual(self.deserialize(resp)['status'], 'FAILED')
        self.assertEqual(self.deserialize(resp)['is_finished'], True)
        self.assertEqual(self.deserialize(resp)['is_running'], False)
        self.assertEqual(self.deserialize(resp)['is_failed'], True)
        self.assertEqual(self.deserialize(resp)['is_successful'], False)

        resp = self.api_client.get('/api/v1/task/%s/messages/' % task.safe_id,
                                   format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertNotEqual(len(self.deserialize(resp)), 0)
        msg = self.deserialize(resp)[0]
        self.assertEqual(msg['level'], 'INFO')
        self.assertTrue(msg['message'].startswith('Starting application'))
        self.assertTrue(msg['timestamp'])

    @pytest.mark.usefixtures("create_user", "create_backend_list")
    def test_backend_list_get(self):
        resp = self.api_client.get('/api/v1/backend/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 10)

    @pytest.mark.usefixtures("create_user", "create_router")
    def test_router_list_get(self):
        resp = self.api_client.get('/api/v1/router/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    @pytest.mark.usefixtures("create_user", "create_run_plan")
    def test_run_plan_list_get(self):
        resp = self.api_client.get('/api/v1/run_plan/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
