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
from apmecclient.common import exceptions

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file

import time
CONF = cfg.CONF


class MesdTestCreate(base.BaseApmecTest):
    def _test_create_tosca_mead(self, tosca_mead_file, mead_name):
        input_yaml = read_file(tosca_mead_file)
        tosca_dict = yaml.safe_load(input_yaml)
        tosca_arg = {'mead': {'name': mead_name,
                              'attributes': {'mead': tosca_dict}}}
        mead_instance = self.client.create_mead(body=tosca_arg)
        self.assertEqual(mead_instance['mead']['name'], mead_name)
        self.assertIsNotNone(mead_instance)

        meads = self.client.list_meads().get('meads')
        self.assertIsNotNone(meads, "List of meads are Empty after Creation")
        return mead_instance['mead']['id']

    def _test_create_mesd(self, tosca_mesd_file, mesd_name):
        input_yaml = read_file(tosca_mesd_file)
        tosca_dict = yaml.safe_load(input_yaml)
        tosca_arg = {'mesd': {'name': mesd_name,
                             'attributes': {'mesd': tosca_dict}}}
        mesd_instance = self.client.create_mesd(body=tosca_arg)
        self.assertIsNotNone(mesd_instance)
        return mesd_instance['mesd']['id']

    def _test_delete_mesd(self, mesd_id):
        try:
            self.client.delete_mesd(mesd_id)
        except Exception:
                assert False, "mesd Delete failed"

    def _test_delete_mead(self, mead_id, timeout=constants.MES_DELETE_TIMEOUT):
        start_time = int(time.time())
        while True:
            try:
                self.client.delete_mead(mead_id)
            except exceptions.Conflict:
                time.sleep(2)
            except Exception:
                assert False, "mead Delete failed"
            else:
                break
            if (int(time.time()) - start_time) > timeout:
                assert False, "mead still in use"
        self.verify_mead_events(mead_id, evt_constants.RES_EVT_DELETE,
                                evt_constants.RES_EVT_NA_STATE)

    def _wait_until_mes_status(self, mes_id, target_status, timeout,
                              sleep_interval):
        start_time = int(time.time())
        while True:
                mes_result = self.client.show_mes(mes_id)
                status = mes_result['mes']['status']
                if (status == target_status) or (
                        (int(time.time()) - start_time) > timeout):
                    break
                time.sleep(sleep_interval)

        self.assertEqual(status, target_status,
                         "mes %(mes_id)s with status %(status)s is"
                         " expected to be %(target)s" %
                         {"mes_id": mes_id, "status": status,
                          "target": target_status})

    def _wait_until_mes_delete(self, mes_id, timeout):
        start_time = int(time.time())
        while True:
            try:
                mes_result = self.client.show_mes(mes_id)
                time.sleep(2)
            except Exception:
                return
            status = mes_result['mes']['status']
            if (status != 'PENDING_DELETE') or ((
                    int(time.time()) - start_time) > timeout):
                raise Exception("Failed with status: %s" % status)

    def _test_create_delete_mes(self, mesd_file, mes_name,
                               template_source='onboarded'):
        mead1_id = self._test_create_tosca_mead(
            'test-mes-mead1.yaml',
            'test-mes-mead1')
        mead2_id = self._test_create_tosca_mead(
            'test-mes-mead2.yaml',
            'test-mes-mead2')

        if template_source == 'onboarded':
            mesd_id = self._test_create_mesd(
                mesd_file,
                'test-mes-mesd')
            mes_arg = {'mes': {
                'mesd_id': mesd_id,
                'name': mes_name,
                'attributes': {"param_values": {
                    "mesd": {
                        "vl2_name": "net0",
                        "vl1_name": "net_mgmt"}}}}}
            mes_instance = self.client.create_mes(body=mes_arg)
            mes_id = mes_instance['mes']['id']

        if template_source == 'inline':
            input_yaml = read_file(mesd_file)
            template = yaml.safe_load(input_yaml)
            mes_arg = {'mes': {
                'name': mes_name,
                'attributes': {"param_values": {
                    "mesd": {
                        "vl2_name": "net0",
                        "vl1_name": "net_mgmt"}}},
                'mesd_template': template}}
            mes_instance = self.client.create_mes(body=mes_arg)
            mes_id = mes_instance['mes']['id']

        self._wait_until_mes_status(mes_id, 'ACTIVE',
                                   constants.MES_CREATE_TIMEOUT,
                                   constants.ACTIVE_SLEEP_TIME)
        mes_show_out = self.client.show_mes(mes_id)['mes']
        self.assertIsNotNone(mes_show_out['mgmt_urls'])

        try:
            self.client.delete_mes(mes_id)
        except Exception as e:
            print("Exception:", e)
            assert False, "mes Delete failed"
        if template_source == 'onboarded':
            self._wait_until_mes_delete(mes_id, constants.NS_DELETE_TIMEOUT)
            self._test_delete_mesd(mesd_id)
        self._test_delete_mead(mead1_id)
        self._test_delete_mead(mead2_id)

    def test_create_delete_mesd(self):
        mead1_id = self._test_create_tosca_mead(
            'test-mesd-mead1.yaml',
            'test-mesd-mead1')
        mead2_id = self._test_create_tosca_mead(
            'test-mesd-mead2.yaml',
            'test-mesd-mead2')
        mesd_id = self._test_create_mesd(
            'test-mesd.yaml',
            'test-mesd')
        self._test_delete_mesd(mesd_id)
        self._test_delete_mead(mead1_id)
        self._test_delete_mead(mead2_id)

    def test_create_delete_network_service(self):
        self._test_create_delete_mes('test-mes-mesd.yaml',
                                    'test-mes-onboarded',
                                    template_source='onboarded')
        time.sleep(1)
        self._test_create_delete_mes('test-mes-mesd.yaml',
                                    'test-mes-inline',
                                    template_source='inline')
