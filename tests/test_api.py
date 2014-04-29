# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import pytest

from tastypie.test import ResourceTestCase

from upaas_admin.common.tests import MongoEngineTestCase


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
                        ['current_package', 'date_created', 'id', 'metadata',
                         'name', 'owner', 'packages', 'resource_uri',
                         'running_tasks', 'tasks'])

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

    @pytest.mark.usefixtures("create_user")
    def test_task_list_empty_get(self):
        resp = self.api_client.get('/api/v1/task/', format='json',
                                   **self.get_apikey_auth(self.user))
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

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
