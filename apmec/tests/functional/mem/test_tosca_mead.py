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

import time

from oslo_config import cfg
import yaml

from apmec.plugins.common import constants as evt_constants
from apmec.tests.functional import base
from apmec.tests.utils import read_file

CONF = cfg.CONF


class MeadTestCreate(base.BaseApmecTest):
    def _test_create_list_delete_tosca_mead(self, tosca_mead_file, mead_name):
        input_yaml = read_file(tosca_mead_file)
        tosca_dict = yaml.safe_load(input_yaml)
        tosca_arg = {'mead': {'name': mead_name,
                              'attributes': {'mead': tosca_dict}}}
        mead_instance = self.client.create_mead(body=tosca_arg)
        self.assertIsNotNone(mead_instance)

        meads = self.client.list_meads().get('meads')
        self.assertIsNotNone(meads, "List of meads are Empty after Creation")

        mead_id = mead_instance['mead']['id']
        self.verify_mead_events(
            mead_id, evt_constants.RES_EVT_CREATE,
            evt_constants.RES_EVT_ONBOARDED)

        try:
            self.client.delete_mead(mead_id)
        except Exception:
            assert False, "mead Delete failed"
        self.verify_mead_events(mead_id, evt_constants.RES_EVT_DELETE,
                                evt_constants.RES_EVT_NA_STATE)

    def test_tosca_mead(self):
        self._test_create_list_delete_tosca_mead('sample-tosca-mead.yaml',
                                                 'sample-tosca-mead-template')

    def test_tosca_large_mead(self):
        self._test_create_list_delete_tosca_mead(
            'sample-tosca-mead-large-template.yaml',
            'sample-tosca-mead-large-template')

    def test_tosca_re_create_delete_mead(self):
        self._test_create_list_delete_tosca_mead('sample-tosca-mead.yaml',
                                                 'test_mead')
        time.sleep(1)
        self._test_create_list_delete_tosca_mead('sample-tosca-mead.yaml',
                                                 'test_mead')
