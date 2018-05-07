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

import time
import yaml

from keystoneauth1.identity import v3
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
from oslo_config import cfg
from tempest.lib import base

from apmec.plugins.common import constants as evt_constants
from apmec.tests import constants
from apmec.tests.functional import clients
from apmec.tests.utils import read_file
from apmec import version

from apmecclient.v1_0 import client as apmec_client


CONF = cfg.CONF


class BaseApmecTest(base.BaseTestCase):
    """Base test case class for all Apmec API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseApmecTest, cls).setUpClass()
        kwargs = {}

        cfg.CONF(args=['--config-file', '/etc/apmec/apmec.conf'],
                 project='apmec',
                 version='%%prog %s' % version.version_info.release_string(),
                 **kwargs)

        cls.client = cls.apmecclient()
        cls.h_client = cls.heatclient()

    @classmethod
    def get_credentials(cls):
        vim_params = yaml.safe_load(read_file('local-vim.yaml'))
        vim_params['auth_url'] += '/v3'
        return vim_params

    @classmethod
    def apmecclient(cls):
        vim_params = cls.get_credentials()
        auth = v3.Password(auth_url=vim_params['auth_url'],
            username=vim_params['username'],
            password=vim_params['password'],
            project_name=vim_params['project_name'],
            user_domain_name=vim_params['user_domain_name'],
            project_domain_name=vim_params['project_domain_name'])
        auth_ses = session.Session(auth=auth)
        return apmec_client.Client(session=auth_ses)

    @classmethod
    def novaclient(cls):
        vim_params = cls.get_credentials()
        auth = v3.Password(auth_url=vim_params['auth_url'],
            username=vim_params['username'],
            password=vim_params['password'],
            project_name=vim_params['project_name'],
            user_domain_name=vim_params['user_domain_name'],
            project_domain_name=vim_params['project_domain_name'])
        auth_ses = session.Session(auth=auth)
        return nova_client.Client(constants.NOVA_CLIENT_VERSION,
                                  session=auth_ses)

    @classmethod
    def neutronclient(cls):
        vim_params = cls.get_credentials()
        auth = v3.Password(auth_url=vim_params['auth_url'],
            username=vim_params['username'],
            password=vim_params['password'],
            project_name=vim_params['project_name'],
            user_domain_name=vim_params['user_domain_name'],
            project_domain_name=vim_params['project_domain_name'])
        auth_ses = session.Session(auth=auth)
        return neutron_client.Client(session=auth_ses)

    @classmethod
    def heatclient(cls):
        data = yaml.safe_load(read_file('local-vim.yaml'))
        data['auth_url'] = data['auth_url'] + '/v3'
        domain_name = data.pop('domain_name')
        data['user_domain_name'] = domain_name
        data['project_domain_name'] = domain_name
        return clients.OpenstackClients(auth_attr=data).heat

    def wait_until_mea_status(self, mea_id, target_status, timeout,
                              sleep_interval):
        start_time = int(time.time())
        while True:
                mea_result = self.client.show_mea(mea_id)
                status = mea_result['mea']['status']
                if (status == target_status) or (
                        (int(time.time()) - start_time) > timeout):
                    break
                time.sleep(sleep_interval)

        self.assertEqual(status, target_status,
                         "mea %(mea_id)s with status %(status)s is"
                         " expected to be %(target)s" %
                         {"mea_id": mea_id, "status": status,
                          "target": target_status})

    def wait_until_mea_active(self, mea_id, timeout, sleep_interval):
        self.wait_until_mea_status(mea_id, 'ACTIVE', timeout,
                                   sleep_interval)

    def wait_until_mea_delete(self, mea_id, timeout):
        start_time = int(time.time())
        while True:
            try:
                mea_result = self.client.show_mea(mea_id)
                time.sleep(1)
            except Exception:
                return
            status = mea_result['mea']['status']
            if (status != 'PENDING_DELETE') or ((
                    int(time.time()) - start_time) > timeout):
                raise Exception("Failed with status: %s" % status)

    def wait_until_mea_dead(self, mea_id, timeout, sleep_interval):
        self.wait_until_mea_status(mea_id, 'DEAD', timeout,
                                   sleep_interval)

    def validate_mea_instance(self, mead_instance, mea_instance):
        self.assertIsNotNone(mea_instance)
        self.assertIsNotNone(mea_instance['mea']['id'])
        self.assertIsNotNone(mea_instance['mea']['instance_id'])
        self.assertEqual(mea_instance['mea']['mead_id'], mead_instance[
            'mead']['id'])

    def verify_mea_restart(self, mead_instance, mea_instance):
        mea_id = mea_instance['mea']['id']
        self.wait_until_mea_active(
            mea_id,
            constants.MEA_CIRROS_CREATE_TIMEOUT,
            constants.ACTIVE_SLEEP_TIME)
        self.validate_mea_instance(mead_instance, mea_instance)
        self.assertIsNotNone(self.client.show_mea(mea_id)['mea']['mgmt_url'])

        self.wait_until_mea_dead(
            mea_id,
            constants.MEA_CIRROS_DEAD_TIMEOUT,
            constants.DEAD_SLEEP_TIME)
        self.wait_until_mea_active(
            mea_id,
            constants.MEA_CIRROS_CREATE_TIMEOUT,
            constants.ACTIVE_SLEEP_TIME)
        self.validate_mea_instance(mead_instance, mea_instance)

    def verify_mea_monitor_events(self, mea_id, mea_state_list):
        for state in mea_state_list:
            params = {'resource_id': mea_id, 'resource_state': state,
                      'event_type': evt_constants.RES_EVT_MONITOR}
            mea_evt_list = self.client.list_mea_events(**params)
            mesg = ("%s - state transition expected." % state)
            self.assertIsNotNone(mea_evt_list['mea_events'], mesg)

    def verify_mea_crud_events(self, mea_id, evt_type, res_state,
                               tstamp=None, cnt=1):
        params = {'resource_id': mea_id,
                  'resource_state': res_state,
                  'resource_type': evt_constants.RES_TYPE_MEA,
                  'event_type': evt_type}
        if tstamp:
            params['timestamp'] = tstamp

        mea_evt_list = self.client.list_mea_events(**params)

        self.assertIsNotNone(mea_evt_list['mea_events'],
                             "List of MEA events are Empty")
        self.assertEqual(cnt, len(mea_evt_list['mea_events']))

    def verify_mead_events(self, mead_id, evt_type, res_state,
                           tstamp=None, cnt=1):
        params = {'resource_id': mead_id,
                  'resource_state': res_state,
                  'resource_type': evt_constants.RES_TYPE_MEAD,
                  'event_type': evt_type}
        if tstamp:
            params['timestamp'] = tstamp

        mead_evt_list = self.client.list_mead_events(**params)

        self.assertIsNotNone(mead_evt_list['mead_events'],
                             "List of MEAD events are Empty")
        self.assertEqual(cnt, len(mead_evt_list['mead_events']))

    def get_vim(self, vim_list, vim_name):
        if len(vim_list.values()) == 0:
            assert False, "vim_list is Empty: Default VIM is missing"

        for vim_list in vim_list.values():
            for vim in vim_list:
                if vim['name'] == vim_name:
                    return vim
        return None

    def verify_antispoofing_in_stack(self, stack_id, resource_name):
        resource_types = self.h_client.resources
        resource_details = resource_types.get(stack_id=stack_id,
                                              resource_name=resource_name)
        resource_dict = resource_details.to_dict()
        self.assertTrue(resource_dict['attributes']['port_security_enabled'])
