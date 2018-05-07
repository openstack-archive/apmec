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

import json
import time
import unittest

from oslo_config import cfg

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file


CONF = cfg.CONF


class MeaTestToscaScale(base.BaseApmecTest):
    @unittest.skip("Skip and wait for releasing Heat Translator")
    def test_mea_tosca_scale(self):
        data = dict()
        data['tosca'] = read_file('sample-tosca-scale-all.yaml')
        mead_name = 'test_tosca_mea_scale_all'
        toscal = data['tosca']
        tosca_arg = {'mead': {'name': mead_name,
                              'attributes': {'mead': toscal}}}

        # Create mead with tosca template
        mead_instance = self.client.create_mead(body=tosca_arg)
        self.assertIsNotNone(mead_instance)

        # Create mea with mead_id
        mead_id = mead_instance['mead']['id']
        mea_name = 'test_tosca_mea_scale_all'
        mea_arg = {'mea': {'mead_id': mead_id, 'name': mea_name}}
        mea_instance = self.client.create_mea(body=mea_arg)

        self.validate_mea_instance(mead_instance, mea_instance)

        mea_id = mea_instance['mea']['id']

        # TODO(kanagaraj-manickam) once load-balancer support is enabled,
        # update this logic to validate the scaling
        def _wait(count):
            self.wait_until_mea_active(
                mea_id,
                constants.MEA_CIRROS_CREATE_TIMEOUT,
                constants.ACTIVE_SLEEP_TIME)
            mea = self.client.show_mea(mea_id)['mea']

            # {"VDU1": ["10.0.0.14", "10.0.0.5"]}
            self.assertEqual(count, len(json.loads(mea['mgmt_url'])['VDU1']))

        _wait(2)
        # Get nested resources when mea is in active state
        mea_details = self.client.list_mea_resources(mea_id)['resources']
        resources_list = list()
        for mea_detail in mea_details:
            resources_list.append(mea_detail['name'])
        self.assertIn('VDU1', resources_list)

        self.assertIn('CP1', resources_list)
        self.assertIn('SP1_group', resources_list)

        def _scale(type, count):
            body = {"scale": {'type': type, 'policy': 'SP1'}}
            self.client.scale_mea(mea_id, body)
            _wait(count)

        # scale out
        time.sleep(constants.SCALE_WINDOW_SLEEP_TIME)
        _scale('out', 3)

        # scale in
        time.sleep(constants.SCALE_WINDOW_SLEEP_TIME)
        _scale('in', 2)

        # Verifying that as part of SCALE OUT, MEA states  PENDING_SCALE_OUT
        # and ACTIVE occurs and as part of SCALE IN, MEA states
        # PENDING_SCALE_IN and ACTIVE occur.
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_SCALE,
                                    evt_constants.ACTIVE, cnt=2)
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_SCALE,
                                    evt_constants.PENDING_SCALE_OUT, cnt=1)
        self.verify_mea_crud_events(mea_id, evt_constants.RES_EVT_SCALE,
                                    evt_constants.PENDING_SCALE_IN, cnt=1)
        # Delete mea_instance with mea_id
        try:
            self.client.delete_mea(mea_id)
        except Exception:
            assert False, "mea Delete failed"

        # Delete mead_instance
        self.addCleanup(self.client.delete_mead, mead_id)
        self.addCleanup(self.wait_until_mea_delete, mea_id,
                        constants.MEA_CIRROS_DELETE_TIMEOUT)
