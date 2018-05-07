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

from oslo_config import cfg

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file

CONF = cfg.CONF
MEA_CIRROS_CREATE_TIMEOUT = 120


class MeaTestCreate(base.BaseApmecTest):
    def _test_create_delete_mea(self, mea_name, mead_name, vim_id=None):
        data = dict()
        data['tosca'] = read_file('sample-tosca-mead-no-monitor.yaml')
        toscal = data['tosca']
        tosca_arg = {'mead': {'name': mead_name,
                     'attributes': {'mead': toscal}}}

        # Create mead with tosca template
        mead_instance = self.client.create_mead(body=tosca_arg)
        self.assertIsNotNone(mead_instance)

        # Create mea with mead_id
        mead_id = mead_instance['mead']['id']
        mea_arg = {'mea': {'mead_id': mead_id, 'name': mea_name}}
        if vim_id:
            mea_arg['mea']['vim_id'] = vim_id
        mea_instance = self.client.create_mea(body=mea_arg)
        self.validate_mea_instance(mead_instance, mea_instance)

        mea_id = mea_instance['mea']['id']
        self.wait_until_mea_active(
            mea_id,
            constants.MEA_CIRROS_CREATE_TIMEOUT,
            constants.ACTIVE_SLEEP_TIME)
        self.assertIsNotNone(self.client.show_mea(mea_id)['mea']['mgmt_url'])
        if vim_id:
            self.assertEqual(vim_id, mea_instance['mea']['vim_id'])

        # Get mea details when mea is in active state
        mea_details = self.client.list_mea_resources(mea_id)['resources'][0]
        self.assertIn('name', mea_details)
        self.assertIn('id', mea_details)
        self.assertIn('type', mea_details)

        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE,
            evt_constants.PENDING_CREATE, cnt=2)
        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE, evt_constants.ACTIVE)

        # update VIM name when MEAs are active.
        # check for exception.
        vim0_id = mea_instance['mea']['vim_id']
        msg = "VIM %s is still in use by MEA" % vim0_id
        try:
            update_arg = {'vim': {'name': "mea_vim"}}
            self.client.update_vim(vim0_id, update_arg)
        except Exception as err:
            self.assertEqual(err.message, msg)
        else:
            self.assertTrue(
                False,
                "Name of vim(s) with active mea(s) should not be changed!")

        # Delete mea_instance with mea_id
        try:
            self.client.delete_mea(mea_id)
        except Exception:
            assert False, "mea Delete failed"

        self.wait_until_mea_delete(mea_id,
                                   constants.MEA_CIRROS_DELETE_TIMEOUT)
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_DELETE,
                                    evt_constants.PENDING_DELETE, cnt=2)

        # Delete mead_instance
        self.addCleanup(self.client.delete_mead, mead_id)

    def test_create_delete_mea_with_default_vim(self):
        self._test_create_delete_mea(
            mea_name='test_mea_with_cirros_no_monitoring_default_vim',
            mead_name='sample_cirros_mea_no_monitoring_default_vim')

    def test_create_delete_mea_with_vim_id(self):
        vim_list = self.client.list_vims()
        vim0_id = self.get_vim(vim_list, 'VIM0')['id']
        self._test_create_delete_mea(
            vim_id=vim0_id,
            mea_name='test_mea_with_cirros_vim_id',
            mead_name='sample_cirros_mea_no_monitoring_vim_id')
