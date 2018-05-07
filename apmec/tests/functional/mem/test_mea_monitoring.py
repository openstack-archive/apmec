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

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file


class MeaTestPingMonitor(base.BaseApmecTest):

    def _test_mea_with_monitoring(self, mead_file, mea_name):
        data = dict()
        data['tosca'] = read_file(mead_file)
        toscal = data['tosca']
        tosca_arg = {'mead': {'name': mea_name,
                              'attributes': {'mead': toscal}}}

        # Create mead with tosca template
        mead_instance = self.client.create_mead(body=tosca_arg)
        self.assertIsNotNone(mead_instance)

        # Create mea with mead_id
        mead_id = mead_instance['mead']['id']
        mea_arg = {'mea': {'mead_id': mead_id, 'name': mea_name}}
        mea_instance = self.client.create_mea(body=mea_arg)

        # Verify mea goes from ACTIVE->DEAD->ACTIVE states
        self.verify_mea_restart(mead_instance, mea_instance)

        # Delete mea_instance with mea_id
        mea_id = mea_instance['mea']['id']
        try:
            self.client.delete_mea(mea_id)
        except Exception:
            assert False, ("Failed to delete mea %s after the monitor test" %
                           mea_id)

        # Verify MEA monitor events captured for states, ACTIVE and DEAD
        mea_state_list = [evt_constants.ACTIVE, evt_constants.DEAD]
        self.verify_mea_monitor_events(mea_id, mea_state_list)

        # Delete mead_instance
        self.addCleanup(self.client.delete_mead, mead_id)
        self.addCleanup(self.wait_until_mea_delete, mea_id,
            constants.MEA_CIRROS_DELETE_TIMEOUT)

    def test_create_delete_mea_monitoring_tosca_template(self):
        self._test_mea_with_monitoring(
            'sample-tosca-mead-monitor.yaml',
            'ping monitor mea with tosca template')

    def test_create_delete_mea_multi_vdu_monitoring_tosca_template(self):
        self._test_mea_with_monitoring(
            'sample-tosca-mead-multi-vdu-monitoring.yaml',
            'ping monitor multi vdu mea with tosca template')
