# Copyright 2015 Brocade Communications System, Inc.
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

from datetime import datetime

import mock
from mock import patch
from oslo_utils import uuidutils
import yaml

from apmec import context
from apmec.db.common_services import common_services_db_plugin
from apmec.db.meo import meo_db
from apmec.db.mem import mem_db
from apmec.extensions import mem
from apmec.plugins.common import constants
from apmec.tests.unit.db import base as db_base
from apmec.tests.unit.db import utils
from apmec.mem import plugin


class FakeDriverManager(mock.Mock):
    def invoke(self, *args, **kwargs):
        if 'create' in args:
            return uuidutils.generate_uuid()

        if 'get_resource_info' in args:
            return {'resources': {'name': 'dummy_mea',
                                  'type': 'dummy',
                                  'id': uuidutils.generate_uuid()}}


class FakeMEAMonitor(mock.Mock):
    pass


class FakeGreenPool(mock.Mock):
    pass


class FakeVimClient(mock.Mock):
    pass


class TestMEMPlugin(db_base.SqlTestCase):
    def setUp(self):
        super(TestMEMPlugin, self).setUp()
        self.addCleanup(mock.patch.stopall)
        self.context = context.get_admin_context()
        self._mock_vim_client()
        self._stub_get_vim()
        self._mock_device_manager()
        self._mock_mea_monitor()
        self._mock_mea_alarm_monitor()
        self._mock_green_pool()
        self._insert_dummy_vim()
        self.mem_plugin = plugin.MEMPlugin()
        mock.patch('apmec.db.common_services.common_services_db_plugin.'
                   'CommonServicesPluginDb.create_event'
                   ).start()
        self._cos_db_plugin =\
            common_services_db_plugin.CommonServicesPluginDb()

    def _mock_device_manager(self):
        self._device_manager = mock.Mock(wraps=FakeDriverManager())
        self._device_manager.__contains__ = mock.Mock(
            return_value=True)
        fake_device_manager = mock.Mock()
        fake_device_manager.return_value = self._device_manager
        self._mock(
            'apmec.common.driver_manager.DriverManager', fake_device_manager)

    def _mock_vim_client(self):
        self.vim_client = mock.Mock(wraps=FakeVimClient())
        fake_vim_client = mock.Mock()
        fake_vim_client.return_value = self.vim_client
        self._mock(
            'apmec.mem.vim_client.VimClient', fake_vim_client)

    def _stub_get_vim(self):
        vim_obj = {'vim_id': '6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                   'vim_name': 'fake_vim', 'vim_auth':
                   {'auth_url': 'http://localhost:5000', 'password':
                       'test_pw', 'username': 'test_user', 'project_name':
                       'test_project'}, 'vim_type': 'test_vim'}
        self.vim_client.get_vim.return_value = vim_obj

    def _mock_green_pool(self):
        self._pool = mock.Mock(wraps=FakeGreenPool())
        fake_green_pool = mock.Mock()
        fake_green_pool.return_value = self._pool
        self._mock(
            'eventlet.GreenPool', fake_green_pool)

    def _mock_mea_monitor(self):
        self._mea_monitor = mock.Mock(wraps=FakeMEAMonitor())
        fake_mea_monitor = mock.Mock()
        fake_mea_monitor.return_value = self._mea_monitor
        self._mock(
            'apmec.mem.monitor.MEAMonitor', fake_mea_monitor)

    def _mock_mea_alarm_monitor(self):
        self._mea_alarm_monitor = mock.Mock(wraps=FakeMEAMonitor())
        fake_mea_alarm_monitor = mock.Mock()
        fake_mea_alarm_monitor.return_value = self._mea_alarm_monitor
        self._mock(
            'apmec.mem.monitor.MEAAlarmMonitor', fake_mea_alarm_monitor)

    def _insert_dummy_device_template(self):
        session = self.context.session
        device_template = mem_db.MEAD(
            id='eb094833-995e-49f0-a047-dfb56aaf7c4e',
            tenant_id='ad7ebc56538745a08ef7c5e97f8bd437',
            name='fake_template',
            description='fake_template_description',
            template_source='onboarded',
            deleted_at=datetime.min)
        session.add(device_template)
        session.flush()
        return device_template

    def _insert_dummy_device_template_inline(self):
        session = self.context.session
        device_template = mem_db.MEAD(
            id='d58bcc4e-d0cf-11e6-bf26-cec0c932ce01',
            tenant_id='ad7ebc56538745a08ef7c5e97f8bd437',
            name='tmpl-koeak4tqgoqo8cr4-dummy_inline_mea',
            description='inline_fake_template_description',
            deleted_at=datetime.min,
            template_source='inline')
        session.add(device_template)
        session.flush()
        return device_template

    def _insert_dummy_mead_attributes(self, template):
        session = self.context.session
        mead_attr = mem_db.MEADAttribute(
            id='eb094833-995e-49f0-a047-dfb56aaf7c4e',
            mead_id='eb094833-995e-49f0-a047-dfb56aaf7c4e',
            key='mead',
            value=template)
        session.add(mead_attr)
        session.flush()
        return mead_attr

    def _insert_dummy_device(self):
        session = self.context.session
        device_db = mem_db.MEA(
            id='6261579e-d6f3-49ad-8bc3-a9cb974778fe',
            tenant_id='ad7ebc56538745a08ef7c5e97f8bd437',
            name='fake_device',
            description='fake_device_description',
            instance_id='da85ea1a-4ec4-4201-bbb2-8d9249eca7ec',
            mead_id='eb094833-995e-49f0-a047-dfb56aaf7c4e',
            vim_id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            placement_attr={'region': 'RegionOne'},
            status='ACTIVE',
            deleted_at=datetime.min)
        session.add(device_db)
        session.flush()
        return device_db

    def _insert_scaling_attributes_mea(self):
        session = self.context.session
        mea_attributes = mem_db.MEAAttribute(
            id='7800cb81-7ed1-4cf6-8387-746468522651',
            mea_id='6261579e-d6f3-49ad-8bc3-a9cb974778fe',
            key='scaling_group_names',
            value='{"SP1": "G1"}'
        )
        session.add(mea_attributes)
        session.flush()
        return mea_attributes

    def _insert_scaling_attributes_mead(self):
        session = self.context.session
        mead_attributes = mem_db.MEADAttribute(
            id='7800cb81-7ed1-4cf6-8387-746468522650',
            mead_id='eb094833-995e-49f0-a047-dfb56aaf7c4e',
            key='mead',
            value=utils.mead_scale_tosca_template
        )
        session.add(mead_attributes)
        session.flush()
        return mead_attributes

    def _insert_dummy_vim(self):
        session = self.context.session
        vim_db = meo_db.Vim(
            id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            tenant_id='ad7ebc56538745a08ef7c5e97f8bd437',
            name='fake_vim',
            description='fake_vim_description',
            type='test_vim',
            status='Active',
            deleted_at=datetime.min,
            placement_attr={'regions': ['RegionOne']})
        vim_auth_db = meo_db.VimAuth(
            vim_id='6261579e-d6f3-49ad-8bc3-a9cb974778ff',
            password='encrypted_pw',
            auth_url='http://localhost:5000',
            vim_project={'name': 'test_project'},
            auth_cred={'username': 'test_user', 'user_domain_id': 'default',
                       'project_domain_id': 'default'})
        session.add(vim_db)
        session.add(vim_auth_db)
        session.flush()

    @mock.patch('apmec.mem.plugin.toscautils.updateimports')
    @mock.patch('apmec.mem.plugin.ToscaTemplate')
    @mock.patch('apmec.mem.plugin.toscautils.get_mgmt_driver')
    def test_create_mead(self, mock_get_mgmt_driver, mock_tosca_template,
                        mock_update_imports):
        mock_get_mgmt_driver.return_value = 'dummy_mgmt_driver'
        mock_tosca_template.return_value = mock.ANY

        mead_obj = utils.get_dummy_mead_obj()
        result = self.mem_plugin.create_mead(self.context, mead_obj)
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        self.assertEqual('dummy_mead', result['name'])
        self.assertEqual('dummy_mead_description', result['description'])
        self.assertEqual('dummy_mgmt_driver', result['mgmt_driver'])
        self.assertIn('service_types', result)
        self.assertIn('attributes', result)
        self.assertIn('created_at', result)
        self.assertIn('updated_at', result)
        self.assertIn('template_source', result)
        yaml_dict = yaml.safe_load(utils.tosca_mead_openwrt)
        mock_tosca_template.assert_called_once_with(
            a_file=False, yaml_dict_tpl=yaml_dict)
        mock_get_mgmt_driver.assert_called_once_with(mock.ANY)
        mock_update_imports.assert_called_once_with(yaml_dict)
        self._cos_db_plugin.create_event.assert_called_once_with(
            self.context, evt_type=constants.RES_EVT_CREATE, res_id=mock.ANY,
            res_state=constants.RES_EVT_ONBOARDED,
            res_type=constants.RES_TYPE_MEAD, tstamp=mock.ANY)

    def test_create_mead_no_service_types(self):
        mead_obj = utils.get_dummy_mead_obj()
        mead_obj['mead'].pop('service_types')
        self.assertRaises(mem.ServiceTypesNotSpecified,
                          self.mem_plugin.create_mead,
                          self.context, mead_obj)

    def test_create_mea_with_mead(self):
        self._insert_dummy_device_template()
        mea_obj = utils.get_dummy_mea_obj()
        result = self.mem_plugin.create_mea(self.context, mea_obj)
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        self.assertIn('instance_id', result)
        self.assertIn('status', result)
        self.assertIn('attributes', result)
        self.assertIn('mgmt_url', result)
        self.assertIn('created_at', result)
        self.assertIn('updated_at', result)
        self._device_manager.invoke.assert_called_with('test_vim',
                                                       'create',
                                                       plugin=mock.ANY,
                                                       context=mock.ANY,
                                                       mea=mock.ANY,
                                                       auth_attr=mock.ANY)
        self._pool.spawn_n.assert_called_once_with(mock.ANY)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_CREATE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_MEA,
            tstamp=mock.ANY, details=mock.ANY)

    @mock.patch('apmec.mem.plugin.MEMPlugin.create_mead')
    def test_create_mea_from_template(self, mock_create_mead):
        self._insert_dummy_device_template_inline()
        mock_create_mead.return_value = {'id':
                'd58bcc4e-d0cf-11e6-bf26-cec0c932ce01'}
        mea_obj = utils.get_dummy_inline_mea_obj()
        result = self.mem_plugin.create_mea(self.context, mea_obj)
        self.assertIsNotNone(result)
        self.assertIn('id', result)
        self.assertIn('instance_id', result)
        self.assertIn('status', result)
        self.assertIn('attributes', result)
        self.assertIn('mgmt_url', result)
        self.assertIn('created_at', result)
        self.assertIn('updated_at', result)
        mock_create_mead.assert_called_once_with(mock.ANY, mock.ANY)
        self._device_manager.invoke.assert_called_with('test_vim',
                                                       'create',
                                                       plugin=mock.ANY,
                                                       context=mock.ANY,
                                                       mea=mock.ANY,
                                                       auth_attr=mock.ANY)
        self._pool.spawn_n.assert_called_once_with(mock.ANY)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_CREATE,
            res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_MEA,
            tstamp=mock.ANY, details=mock.ANY)

    def test_show_mea_details_mea_inactive(self):
        self._insert_dummy_device_template()
        mea_obj = utils.get_dummy_mea_obj()
        result = self.mem_plugin.create_mea(self.context, mea_obj)
        self.assertRaises(mem.MEAInactive, self.mem_plugin.get_mea_resources,
                          self.context, result['id'])

    def test_show_mea_details_mea_active(self):
        self._insert_dummy_device_template()
        active_mea = self._insert_dummy_device()
        resources = self.mem_plugin.get_mea_resources(self.context,
                                                       active_mea['id'])[0]
        self.assertIn('name', resources)
        self.assertIn('type', resources)
        self.assertIn('id', resources)

    def test_delete_mea(self):
        self._insert_dummy_device_template()
        dummy_device_obj = self._insert_dummy_device()
        self.mem_plugin.delete_mea(self.context, dummy_device_obj[
            'id'])
        self._device_manager.invoke.assert_called_with('test_vim', 'delete',
                                                       plugin=mock.ANY,
                                                       context=mock.ANY,
                                                       mea_id=mock.ANY,
                                                       auth_attr=mock.ANY,
                                                       region_name=mock.ANY)
        self._mea_monitor.delete_hosting_mea.assert_called_with(mock.ANY)
        self._pool.spawn_n.assert_called_once_with(mock.ANY, mock.ANY,
                                                   mock.ANY, mock.ANY,
                                                   mock.ANY)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_DELETE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_MEA,
            tstamp=mock.ANY, details=mock.ANY)

    def test_update_mea(self):
        self._insert_dummy_device_template()
        dummy_device_obj = self._insert_dummy_device()
        mea_config_obj = utils.get_dummy_mea_config_obj()
        result = self.mem_plugin.update_mea(self.context, dummy_device_obj[
            'id'], mea_config_obj)
        self.assertIsNotNone(result)
        self.assertEqual(dummy_device_obj['id'], result['id'])
        self.assertIn('instance_id', result)
        self.assertIn('status', result)
        self.assertIn('attributes', result)
        self.assertIn('mgmt_url', result)
        self.assertIn('updated_at', result)
        self._pool.spawn_n.assert_called_once_with(mock.ANY, mock.ANY,
                                                   mock.ANY, mock.ANY,
                                                   mock.ANY)
        self._cos_db_plugin.create_event.assert_called_with(
            self.context, evt_type=constants.RES_EVT_UPDATE, res_id=mock.ANY,
            res_state=mock.ANY, res_type=constants.RES_TYPE_MEA,
            tstamp=mock.ANY)

    def _get_dummy_scaling_policy(self, type):
        mea_scale = {}
        mea_scale['scale'] = {}
        mea_scale['scale']['type'] = type
        mea_scale['scale']['policy'] = 'SP1'
        return mea_scale

    def _test_scale_mea(self, type, scale_state):
        # create mead
        self._insert_dummy_device_template()
        self._insert_scaling_attributes_mead()

        # create mea
        dummy_device_obj = self._insert_dummy_device()
        self._insert_scaling_attributes_mea()

        # scale mea
        mea_scale = self._get_dummy_scaling_policy(type)
        self.mem_plugin.create_mea_scale(
            self.context,
            dummy_device_obj['id'],
            mea_scale)

        # validate
        self._device_manager.invoke.assert_called_once_with(
            mock.ANY,
            'scale',
            plugin=mock.ANY,
            context=mock.ANY,
            auth_attr=mock.ANY,
            policy=mock.ANY,
            region_name=mock.ANY
        )

        self._pool.spawn_n.assert_called_once_with(mock.ANY)

        self._cos_db_plugin.create_event.assert_called_with(
            self.context,
            evt_type=constants.RES_EVT_SCALE,
            res_id='6261579e-d6f3-49ad-8bc3-a9cb974778fe',
            res_state=scale_state,
            res_type=constants.RES_TYPE_MEA,
            tstamp=mock.ANY)

    def test_scale_mea_out(self):
        self._test_scale_mea('out', constants.PENDING_SCALE_OUT)

    def test_scale_mea_in(self):
        self._test_scale_mea('in', constants.PENDING_SCALE_IN)

    def _get_dummy_active_mea(self, mead_template):
        dummy_mea = utils.get_dummy_device_obj()
        dummy_mea['mead']['attributes']['mead'] = mead_template
        dummy_mea['status'] = 'ACTIVE'
        dummy_mea['instance_id'] = '4c00108e-c69d-4624-842d-389c77311c1d'
        dummy_mea['vim_id'] = '437ac8ef-a8fb-4b6e-8d8a-a5e86a376e8b'
        return dummy_mea

    def _test_create_mea_trigger(self, policy_name, action_value):
        mea_id = "6261579e-d6f3-49ad-8bc3-a9cb974778fe"
        trigger_request = {"trigger": {"action_name": action_value, "params": {
            "credential": "026kll6n", "data": {"current": "alarm",
                                               'alarm_id':
                                    "b7fa9ffd-0a4f-4165-954b-5a8d0672a35f"}},
            "policy_name": policy_name}}
        expected_result = {"action_name": action_value, "params": {
            "credential": "026kll6n", "data": {"current": "alarm",
            "alarm_id": "b7fa9ffd-0a4f-4165-954b-5a8d0672a35f"}},
            "policy_name": policy_name}
        self._mea_alarm_monitor.process_alarm_for_mea.return_value = True
        trigger_result = self.mem_plugin.create_mea_trigger(
            self.context, mea_id, trigger_request)
        self.assertEqual(expected_result, trigger_result)

    @patch('apmec.db.mem.mem_db.MEMPluginDb.get_mea')
    def test_create_mea_trigger_respawn(self, mock_get_mea):
        dummy_mea = self._get_dummy_active_mea(
            utils.mead_alarm_respawn_tosca_template)
        mock_get_mea.return_value = dummy_mea
        self._test_create_mea_trigger(policy_name="vdu_hcpu_usage_respawning",
                                      action_value="respawn")

    @patch('apmec.db.mem.mem_db.MEMPluginDb.get_mea')
    def test_create_mea_trigger_scale(self, mock_get_mea):
        dummy_mea = self._get_dummy_active_mea(
            utils.mead_alarm_scale_tosca_template)
        mock_get_mea.return_value = dummy_mea
        self._test_create_mea_trigger(policy_name="vdu_hcpu_usage_scaling_out",
                                      action_value="SP1-out")

    @patch('apmec.db.mem.mem_db.MEMPluginDb.get_mea')
    def test_create_mea_trigger_multi_actions(self, mock_get_mea):
        dummy_mea = self._get_dummy_active_mea(
            utils.mead_alarm_multi_actions_tosca_template)
        mock_get_mea.return_value = dummy_mea
        self._test_create_mea_trigger(policy_name="mon_policy_multi_actions",
                                      action_value="respawn&log")

    @patch('apmec.db.mem.mem_db.MEMPluginDb.get_mea')
    def test_get_mea_policies(self, mock_get_mea):
        mea_id = "6261579e-d6f3-49ad-8bc3-a9cb974778fe"
        dummy_mea = self._get_dummy_active_mea(
            utils.mead_alarm_respawn_tosca_template)
        mock_get_mea.return_value = dummy_mea
        policies = self.mem_plugin.get_mea_policies(self.context, mea_id,
            filters={'name': 'vdu1_cpu_usage_monitoring_policy'})
        self.assertEqual(1, len(policies))
