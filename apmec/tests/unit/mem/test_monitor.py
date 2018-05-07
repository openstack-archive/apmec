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
#

import json

import mock
from oslo_utils import timeutils
import testtools

from apmec.db.common_services import common_services_db_plugin
from apmec.plugins.common import constants
from apmec.mem import monitor

MOCK_DEVICE_ID = 'a737497c-761c-11e5-89c3-9cb6541d805d'
MOCK_MEA_DEVICE = {
    'id': MOCK_DEVICE_ID,
    'management_ip_addresses': {
        'vdu1': 'a.b.c.d'
    },
    'monitoring_policy': {
        'vdus': {
            'vdu1': {
                'ping': {
                    'actions': {
                        'failure': 'respawn'
                    },
                    'monitoring_params': {
                        'count': 1,
                        'monitoring_delay': 0,
                        'interval': 0,
                        'timeout': 2
                    }
                }
            }
        }
    },
    'boot_at': timeutils.utcnow(),
    'action_cb': mock.MagicMock()
}


class TestMEAMonitor(testtools.TestCase):

    def setUp(self):
        super(TestMEAMonitor, self).setUp()
        p = mock.patch('apmec.common.driver_manager.DriverManager')
        self.mock_monitor_manager = p.start()
        mock.patch('apmec.db.common_services.common_services_db_plugin.'
                   'CommonServicesPluginDb.create_event'
                   ).start()
        self._cos_db_plugin =\
            common_services_db_plugin.CommonServicesPluginDb()
        self.addCleanup(p.stop)

    def test_to_hosting_mea(self):
        test_device_dict = {
            'id': MOCK_DEVICE_ID,
            'mgmt_url': '{"vdu1": "a.b.c.d"}',
            'attributes': {
                'monitoring_policy': json.dumps(
                        MOCK_MEA_DEVICE['monitoring_policy'])
            }
        }
        action_cb = mock.MagicMock()
        expected_output = {
            'id': MOCK_DEVICE_ID,
            'action_cb': action_cb,
            'management_ip_addresses': {
                'vdu1': 'a.b.c.d'
            },
            'mea': test_device_dict,
            'monitoring_policy': MOCK_MEA_DEVICE['monitoring_policy']
        }
        output_dict = monitor.MEAMonitor.to_hosting_mea(test_device_dict,
                                                action_cb)
        self.assertEqual(expected_output, output_dict)

    @mock.patch('apmec.mem.monitor.MEAMonitor.__run__')
    def test_add_hosting_mea(self, mock_monitor_run):
        test_device_dict = {
            'id': MOCK_DEVICE_ID,
            'mgmt_url': '{"vdu1": "a.b.c.d"}',
            'attributes': {
                'monitoring_policy': json.dumps(
                        MOCK_MEA_DEVICE['monitoring_policy'])
            },
            'status': 'ACTIVE'
        }
        action_cb = mock.MagicMock()
        test_boot_wait = 30
        test_memonitor = monitor.MEAMonitor(test_boot_wait)
        new_dict = test_memonitor.to_hosting_mea(test_device_dict, action_cb)
        test_memonitor.add_hosting_mea(new_dict)
        test_device_id = list(test_memonitor._hosting_meas.keys())[0]
        self.assertEqual(MOCK_DEVICE_ID, test_device_id)
        self._cos_db_plugin.create_event.assert_called_with(
            mock.ANY, res_id=mock.ANY, res_type=constants.RES_TYPE_MEA,
            res_state=mock.ANY, evt_type=constants.RES_EVT_MONITOR,
            tstamp=mock.ANY, details=mock.ANY)

    @mock.patch('apmec.mem.monitor.MEAMonitor.__run__')
    def test_run_monitor(self, mock_monitor_run):
        test_hosting_mea = MOCK_MEA_DEVICE
        test_hosting_mea['mea'] = {}
        test_boot_wait = 30
        mock_kwargs = {
            'count': 1,
            'monitoring_delay': 0,
            'interval': 0,
            'mgmt_ip': 'a.b.c.d',
            'timeout': 2
        }
        test_memonitor = monitor.MEAMonitor(test_boot_wait)
        self.mock_monitor_manager.invoke = mock.MagicMock()
        test_memonitor._monitor_manager = self.mock_monitor_manager
        test_memonitor.run_monitor(test_hosting_mea)
        self.mock_monitor_manager\
            .invoke.assert_called_once_with('ping', 'monitor_call', mea={},
                                            kwargs=mock_kwargs)
