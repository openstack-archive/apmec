# Copyright 2016 Brocade Communications System, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import codecs
from datetime import datetime
import mock
import os
from oslo_utils import uuidutils

from mock import patch

from apmec import context
from apmec.db.common_services import common_services_db_plugin
from apmec.db.meo import meo_db
from apmec.extensions import meo
from apmec.meo import meo_plugin
from apmec.plugins.common import constants
from apmec.tests.unit.db import base as db_base
from apmec.tests.unit.db import utils

SECRET_PASSWORD = '***'
DUMMY_mes_2 = 'ba6bf017-f6f7-45f1-a280-57b073bf78ef'


def dummy_get_vim(*args, **kwargs):
    vim_obj = dict()
    vim_obj['auth_cred'] = utils.get_vim_auth_obj()
    vim_obj['type'] = 'openstack'
    return vim_obj


def _get_template(name):
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                '../../etc/samples/' + str(name)))
    f = codecs.open(filename, encoding='utf-8', errors='strict')
    return f.read()


class FakeDriverManager(mock.Mock):
    def invoke(self, *args, **kwargs):
        if any(x in ['create', 'create_chain', 'create_flow_classifier'] for
               x in args):
            return uuidutils.generate_uuid()
        elif 'execute_workflow' in args:
            mock_execution = mock.Mock()
            mock_execution.id.return_value = \
                "ba6bf017-f6f7-45f1-a280-57b073bf78ea"
            return mock_execution
        elif ('prepare_and_create_workflow' in args and
              'delete' == kwargs['action'] and
              DUMMY_mes_2 == kwargs['kwargs']['mes']['id']):
            raise meo.NoTasksException()
        elif ('prepare_and_create_workflow' in args and
              'create' == kwargs['action'] and
              utils.DUMMY_mes_2_NAME == kwargs['kwargs']['mes']['mes']['name']):
            raise meo.NoTasksException()


def get_by_name():
    return False


def get_by_id():
    return False


def dummy_get_vim_auth(*args, **kwargs):
    return {'vim_auth': {u'username': u'admin', 'password': 'devstack',
                         u'project_name': u'mec', u'user_id': u'',
                         u'user_domain_name': u'Default',
                         u'auth_url': u'http://10.0.4.207/identity/v3',
                         u'project_id': u'',
                         u'project_domain_name': u'Default'},
            'vim_id': u'96025dd5-ca16-49f3-9823-958eb04260c4',
            'vim_type': u'openstack', 'vim_name': u'VIM0'}


class FakeClient(mock.Mock):
    def __init__(self, auth):
        pass


class FakeMEMPlugin(mock.Mock):

    def __init__(self):
        super(FakeMEMPlugin, self).__init__()
        self.mea1_mead_id = 'eb094833-995e-49f0-a047-dfb56aaf7c4e'
        self.mea1_mea_id = '91e32c20-6d1f-47a4-9ba7-08f5e5effe07'
        self.mea3_mead_id = 'e4015e9f-1ef2-49fb-adb6-070791ad3c45'
        self.mea2_mead_id = 'e4015e9f-1ef2-49fb-adb6-070791ad3c45'
        self.mea3_mea_id = '7168062e-9fa1-4203-8cb7-f5c99ff3ee1b'
        self.mea3_update_mea_id = '10f66bc5-b2f1-45b7-a7cd-6dd6ad0017f5'

        self.cp11_id = 'd18c8bae-898a-4932-bff8-d5eac981a9c9'
        self.cp12_id = 'c8906342-3e30-4b2a-9401-a251a7a9b5dd'
        self.cp32_id = '3d1bd2a2-bf0e-44d1-87af-a2c6b2cad3ed'
        self.cp32_update_id = '064c0d99-5a61-4711-9597-2a44dc5da14b'

    def get_mead(self, *args, **kwargs):
        if 'MEA1' in args:
            return {'id': self.mea1_mead_id,
                    'name': 'MEA1',
                    'attributes': {'mead': _get_template(
                                   'test-mesd-mead1.yaml')}}
        elif 'MEA2' in args:
            return {'id': self.mea3_mead_id,
                    'name': 'MEA2',
                    'attributes': {'mead': _get_template(
                                   'test-mesd-mead2.yaml')}}

    def get_meads(self, *args, **kwargs):
        if {'name': ['MEA1']} in args:
            return [{'id': self.mea1_mead_id}]
        elif {'name': ['MEA3']} in args:
            return [{'id': self.mea3_mead_id}]
        else:
            return []

    def get_meas(self, *args, **kwargs):
        if {'mead_id': [self.mea1_mead_id]} in args:
            return [{'id': self.mea1_mea_id}]
        elif {'mead_id': [self.mea3_mead_id]} in args:
            return [{'id': self.mea3_mea_id}]
        else:
            return None

    def get_mea(self, *args, **kwargs):
        if self.mea1_mea_id in args:
            return self.get_dummy_mea1()
        elif self.mea3_mea_id in args:
            return self.get_dummy_mea3()
        elif self.mea3_update_mea_id in args:
            return self.get_dummy_mea3_update()

    def get_mea_resources(self, *args, **kwargs):
        if self.mea1_mea_id in args:
            return self.get_dummy_mea1_details()
        elif self.mea3_mea_id in args:
            return self.get_dummy_mea3_details()
        elif self.mea3_update_mea_id in args:
            return self.get_dummy_mea3_update_details()

    def get_dummy_mea1_details(self):
        return [{'name': 'CP11', 'id': self.cp11_id},
                {'name': 'CP12', 'id': self.cp12_id}]

    def get_dummy_mea3_details(self):
        return [{'name': 'CP32', 'id': self.cp32_id}]

    def get_dummy_mea3_update_details(self):
        return [{'name': 'CP32', 'id': self.cp32_update_id}]

    def get_dummy_mea1(self):
        return {'description': 'dummy_mea_description',
                'mead_id': self.mea1_mead_id,
                'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                'name': 'dummy_mea1',
                'attributes': {}}

    def get_dummy_mea3(self):
        return {'description': 'dummy_mea_description',
                'mead_id': self.mea3_mead_id,
                'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                'name': 'dummy_mea2',
                'attributes': {}}

    def get_dummy_mea3_update(self):
        return {'description': 'dummy_mea_description',
                'mead_id': self.mea3_mead_id,
                'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                'name': 'dummy_mea_update',
                'attributes': {}}


class TestMeoPlugin(db_base.SqlTestCase):
    def setUp(self):
        super(TestMeoPlugin, self).setUp()
        self.addCleanup(mock.patch.stopall)
        self.context = context.get_admin_context()
        self._mock_driver_manager()
        mock.patch('apmec.meo.meo_plugin.MeoPlugin._get_vim_from_mea',
                   side_effect=dummy_get_vim).start()
        self.meo_plugin = meo_plugin.MeoPlugin()
        mock.patch('apmec.db.common_services.common_services_db_plugin.'
                   'CommonServicesPluginDb.create_event'
                   ).start()
        self._cos_db_plugin =\
            common_services_db_plugin.CommonServicesPluginDb()

    def _mock_driver_manager(self):
        self._driver_manager = mock.Mock(wraps=FakeDriverManager())
        self._driver_manager.__contains__ = mock.Mock(
            return_value=True)
        fake_driver_manager = mock.Mock()
        fake_driver_manager.return_value = self._driver_manager
        self._mock(
            'apmec.common.driver_manager.DriverManager', fake_driver_manager)

    def _insert_dummy_vim(self):
        session = self.context.session
        vim_db = meo_db.Vim(
            id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            tenant_id='ad7ebc56538745a08ef7c5e97f8bd437',
            name='fake_vim',
            description='fake_vim_description',
            type='openstack',
            status='Active',
            deleted_at=datetime.min,
            placement_attr={'regions': ['RegionOne']})
        vim_auth_db = meo_db.VimAuth(
            vim_id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            password='encrypted_pw',
            auth_url='http://localhost:5000',
            vim_project={'name': 'test_project'},
            auth_cred={'username': 'test_user', 'user_domain_id': 'default',
                       'project_domain_id': 'default',
                       'key_type': 'fernet_key'})
        session.add(vim_db)
        session.add(vim_auth_db)
        session.flush()

    def _insert_dummy_vim_barbican(self):
        session = self.context.session
        vim_db = meo_db.Vim(
            id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            tenant_id='ad7ebc56538745a08ef7c5e97f8bd437',
            name='fake_vim',
            description='fake_vim_description',
            type='openstack',
            status='Active',
            deleted_at=datetime.min,
            placement_attr={'regions': ['RegionOne']})
        vim_auth_db = meo_db.VimAuth(
            vim_id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            password='encrypted_pw',
            auth_url='http://localhost:5000',
            vim_project={'name': 'test_project'},
            auth_cred={'username': 'test_user', 'user_domain_id': 'default',
                       'project_domain_id': 'default',
                       'key_type': 'barbican_key',
                       'secret_uuid': 'fake-secret-uuid'})
        session.add(vim_db)
        session.add(vim_auth_db)
        session.flush()

    def test_create_vim(self):
        vim_dict = utils.get_vim_obj()
        vim_type = 'openstack'
        res = self.meo_plugin.create_vim(self.context, vim_dict)
        self._cos_db_plugin.create_event.assert_any_call(
            self.context, evt_type=constants.RES_EVT_CREATE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_VIM,
            tstamp=mock.ANY)
        self._driver_manager.invoke.assert_any_call(
            vim_type, 'register_vim',
            context=self.context, vim_obj=vim_dict['vim'])
        self.assertIsNotNone(res)
        self.assertEqual(SECRET_PASSWORD, res['auth_cred']['password'])
        self.assertIn('id', res)
        self.assertIn('placement_attr', res)
        self.assertIn('created_at', res)
        self.assertIn('updated_at', res)

    def test_delete_vim(self):
        self._insert_dummy_vim()
        vim_type = u'openstack'
        vim_id = '6261579e-d6f3-49ad-8bc3-a9cb974778ff'
        vim_obj = self.meo_plugin._get_vim(self.context, vim_id)
        self.meo_plugin.delete_vim(self.context, vim_id)
        self._driver_manager.invoke.assert_called_once_with(
            vim_type, 'deregister_vim',
            context=self.context,
            vim_obj=vim_obj)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_DELETE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_VIM,
            tstamp=mock.ANY)

    def test_update_vim(self):
        vim_dict = {'vim': {'id': '6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                            'vim_project': {'name': 'new_project'},
                            'auth_cred': {'username': 'new_user',
                                          'password': 'new_password'}}}
        vim_type = u'openstack'
        vim_auth_username = vim_dict['vim']['auth_cred']['username']
        vim_project = vim_dict['vim']['vim_project']
        self._insert_dummy_vim()
        res = self.meo_plugin.update_vim(self.context, vim_dict['vim']['id'],
                                          vim_dict)
        vim_obj = self.meo_plugin._get_vim(
            self.context, vim_dict['vim']['id'])
        vim_obj['updated_at'] = None
        self._driver_manager.invoke.assert_called_with(
            vim_type, 'register_vim',
            context=self.context,
            vim_obj=vim_obj)
        self.assertIsNotNone(res)
        self.assertIn('id', res)
        self.assertIn('placement_attr', res)
        self.assertEqual(vim_project, res['vim_project'])
        self.assertEqual(vim_auth_username, res['auth_cred']['username'])
        self.assertEqual(SECRET_PASSWORD, res['auth_cred']['password'])
        self.assertIn('updated_at', res)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_UPDATE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_VIM,
            tstamp=mock.ANY)

    def test_update_vim_barbican(self):
        vim_dict = {'vim': {'id': '6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                            'vim_project': {'name': 'new_project'},
                            'auth_cred': {'username': 'new_user',
                                          'password': 'new_password'}}}
        vim_type = u'openstack'
        vim_auth_username = vim_dict['vim']['auth_cred']['username']
        vim_project = vim_dict['vim']['vim_project']
        self._insert_dummy_vim_barbican()
        old_vim_obj = self.meo_plugin._get_vim(
            self.context, vim_dict['vim']['id'])
        res = self.meo_plugin.update_vim(self.context, vim_dict['vim']['id'],
                                          vim_dict)
        vim_obj = self.meo_plugin._get_vim(
            self.context, vim_dict['vim']['id'])
        vim_obj['updated_at'] = None
        self._driver_manager.invoke.assert_called_with(
            vim_type, 'delete_vim_auth',
            context=self.context,
            vim_id=vim_obj['id'],
            auth=old_vim_obj['auth_cred'])
        self.assertIsNotNone(res)
        self.assertIn('id', res)
        self.assertIn('placement_attr', res)
        self.assertEqual(vim_project, res['vim_project'])
        self.assertEqual(vim_auth_username, res['auth_cred']['username'])
        self.assertEqual(SECRET_PASSWORD, res['auth_cred']['password'])
        self.assertIn('updated_at', res)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_UPDATE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_VIM,
            tstamp=mock.ANY)