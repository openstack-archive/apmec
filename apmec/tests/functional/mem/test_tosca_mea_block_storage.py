# Copyright 2016 Brocade Communications System, Inc.
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

from oslo_config import cfg

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file


CONF = cfg.CONF
MEA_CIRROS_CREATE_TIMEOUT = 120


class MeaBlockStorageTestToscaCreate(base.BaseApmecTest):
    def _test_create_mea(self, mead_file, mea_name,
                         template_source="onboarded"):
        data = dict()
        values_str = read_file(mead_file)
        data['tosca'] = values_str
        toscal = data['tosca']
        tosca_arg = {'mead': {'name': mea_name,
                              'attributes': {'mead': toscal}}}

        if template_source == "onboarded":
            # Create mead with tosca template
            mead_instance = self.client.create_mead(body=tosca_arg)
            self.assertIsNotNone(mead_instance)

            # Create mea with mead_id
            mead_id = mead_instance['mead']['id']
            mea_arg = {'mea': {'mead_id': mead_id, 'name': mea_name}}
            mea_instance = self.client.create_mea(body=mea_arg)
            self.validate_mea_instance(mead_instance, mea_instance)

        if template_source == 'inline':
            # create mea directly from template
            template = yaml.safe_load(values_str)
            mea_arg = {'mea': {'mead_template': template, 'name': mea_name}}
            mea_instance = self.client.create_mea(body=mea_arg)
            mead_id = mea_instance['mea']['mead_id']

        mea_id = mea_instance['mea']['id']
        self.wait_until_mea_active(
            mea_id,
            constants.MEA_CIRROS_CREATE_TIMEOUT,
            constants.ACTIVE_SLEEP_TIME)
        mea_show_out = self.client.show_mea(mea_id)['mea']
        self.assertIsNotNone(mea_show_out['mgmt_url'])

        input_dict = yaml.safe_load(values_str)
        prop_dict = input_dict['topology_template']['node_templates'][
            'CP1']['properties']

        # Verify if ip_address is static, it is same as in show_mea
        if prop_dict.get('ip_address'):
            mgmt_url_input = prop_dict.get('ip_address')
            mgmt_info = yaml.safe_load(
                mea_show_out['mgmt_url'])
            self.assertEqual(mgmt_url_input, mgmt_info['VDU1'])

        # Verify anti spoofing settings
        stack_id = mea_show_out['instance_id']
        template_dict = input_dict['topology_template']['node_templates']
        for field in template_dict.keys():
            prop_dict = template_dict[field]['properties']
            if prop_dict.get('anti_spoofing_protection'):
                self.verify_antispoofing_in_stack(stack_id=stack_id,
                                                  resource_name=field)

        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE,
            evt_constants.PENDING_CREATE, cnt=2)
        self.verify_mea_crud_events(
            mea_id, evt_constants.RES_EVT_CREATE, evt_constants.ACTIVE)
        return mead_id, mea_id

    def _test_delete_mea(self, mea_id):
        # Delete mea_instance with mea_id
        try:
            self.client.delete_mea(mea_id)
        except Exception:
            assert False, "mea Delete failed"

        self.wait_until_mea_delete(mea_id,
                                   constants.MEA_CIRROS_DELETE_TIMEOUT)
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_DELETE,
                                    evt_constants.PENDING_DELETE, cnt=2)

    def _test_cleanup_mead(self, mead_id, mea_id):
        # Delete mead_instance
        self.addCleanup(self.client.delete_mead, mead_id)
        self.addCleanup(self.wait_until_mea_delete, mea_id,
            constants.MEA_CIRROS_DELETE_TIMEOUT)

    def _test_create_delete_mea_tosca(self, mead_file, mea_name,
            template_source):
        mead_id, mea_id = self._test_create_mea(mead_file, mea_name,
                                                template_source)
        servers = self.novaclient().servers.list()
        vdus = []
        for server in servers:
            vdus.append(server.name)
        self.assertIn('test-vdu-block-storage', vdus)

        for server in servers:
            if server.name == 'test-vdu-block-storage':
                server_id = server.id
                server_volumes = self.novaclient().volumes\
                    .get_server_volumes(server_id)
                self.assertTrue(len(server_volumes) > 0)
        self._test_delete_mea(mea_id)
        if template_source == "onboarded":
            self._test_cleanup_mead(mead_id, mea_id)

    def test_create_delete_mea_tosca_from_mead(self):
        self._test_create_delete_mea_tosca(
            'sample-tosca-mead-block-storage.yaml',
            'test_tosca_mea_with_cirros',
            'onboarded')
