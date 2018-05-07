# Copyright 2015 Brocade Communications System, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
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

import yaml

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file


class MemTestParam(base.BaseApmecTest):
    def _test_mead_create(self, mead_file, mead_name):
        yaml_input = read_file(mead_file)
        req_dict = {'mead': {'name': mead_name,
                    'attributes': {'mead': yaml_input}}}

        # Create mead
        mead_instance = self.client.create_mead(body=req_dict)
        self.assertIsNotNone(mead_instance)
        mead_id = mead_instance['mead']['id']
        self.assertIsNotNone(mead_id)
        self.verify_mead_events(
            mead_id, evt_constants.RES_EVT_CREATE,
            evt_constants.RES_EVT_ONBOARDED)
        return mead_instance

    def _test_mead_delete(self, mead_instance):
        # Delete mead
        mead_id = mead_instance['mead']['id']
        self.assertIsNotNone(mead_id)
        try:
            self.client.delete_mead(mead_id)
        except Exception:
            assert False, "mead Delete failed"
        self.verify_mead_events(mead_id, evt_constants.RES_EVT_DELETE,
                                evt_constants.RES_EVT_NA_STATE)
        try:
            mead_d = self.client.show_mead(mead_id)
        except Exception:
            assert True, "Mead Delete success" + str(mead_d) + str(Exception)

    def _test_mea_create(self, mead_instance, mea_name, param_values):
        # Create the mea with values
        mead_id = mead_instance['mead']['id']
        # Create mea with values file
        mea_dict = dict()
        mea_dict = {'mea': {'mead_id': mead_id, 'name': mea_name,
                    'attributes': {'param_values': param_values}}}
        mea_instance = self.client.create_mea(body=mea_dict)

        self.validate_mea_instance(mead_instance, mea_instance)
        mea_id = mea_instance['mea']['id']
        self.wait_until_mea_active(
            mea_id,
            constants.MEA_CIRROS_CREATE_TIMEOUT,
            constants.ACTIVE_SLEEP_TIME)
        self.assertIsNotNone(self.client.show_mea(mea_id)['mea']['mgmt_url'])
        mea_instance = self.client.show_mea(mea_id)

        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE,
            evt_constants.PENDING_CREATE, cnt=2)
        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE, evt_constants.ACTIVE)

        # Verify values dictionary is same as param values from mea_show

        param_values = mea_instance['mea']['attributes']['param_values']
        param_values_dict = yaml.safe_load(param_values)

        return mea_instance, param_values_dict

    def _test_mea_delete(self, mea_instance):
        # Delete Mea
        mea_id = mea_instance['mea']['id']
        try:
            self.client.delete_mea(mea_id)
        except Exception:
            assert False, "mea Delete failed"
        self.wait_until_mea_delete(mea_id,
                                   constants.MEA_CIRROS_DELETE_TIMEOUT)
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_DELETE,
                                    evt_constants.PENDING_DELETE, cnt=2)

        try:
            mea_d = self.client.show_mea(mea_id)
        except Exception:
            assert True, "Mea Delete success" + str(mea_d) + str(Exception)

    def test_mead_param_tosca_template(self):
        mead_name = 'sample_cirros_mead_tosca'
        mead_instance = self._test_mead_create(
            'sample-tosca-mead-param.yaml', mead_name)
        self._test_mead_delete(mead_instance)

    def test_mea_param_tosca_template(self):
        mead_name = 'cirros_mead_tosca_param'
        mead_instance = self._test_mead_create(
            'sample-tosca-mead-param.yaml', mead_name)
        values_str = read_file('sample-tosca-mea-values.yaml')
        values_dict = yaml.safe_load(values_str)
        mea_instance, param_values_dict = self._test_mea_create(mead_instance,
                                    'test_mea_with_parameters_tosca_template',
                                                                values_dict)
        self.assertEqual(values_dict, param_values_dict)
        self._test_mea_delete(mea_instance)
        mea_id = mea_instance['mea']['id']
        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE,
            evt_constants.PENDING_CREATE, cnt=2)
        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE, evt_constants.ACTIVE)
        self.wait_until_mea_delete(mea_id,
                                   constants.MEA_CIRROS_DELETE_TIMEOUT)
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_DELETE,
                                    evt_constants.PENDING_DELETE, cnt=2)
        self.addCleanup(self.client.delete_mead, mead_instance['mead']['id'])
