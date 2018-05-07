# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from apmec import context
from apmec.meo.drivers.workflow import workflow_generator
from apmec.tests.unit import base


def get_dummy_mes():
    return {u'mes': {'description': '',
                    'tenant_id': u'a81900a92bda40588c52699e1873a92f',
                    'vim_id': u'96025dd5-ca16-49f3-9823-958eb04260c4',
                    'mea_ids': '', u'attributes': {},
                    u'mesd_id': u'b8587afb-6099-4f56-abce-572c62e3d61d',
                    u'name': u'test_create_mes'},
            'mead_details': {u'mea1': {'instances': ['MEA1'],
                             'id': u'dec09ed4-f355-4ec8-a00b-8548f6575a80'},
            u'mea2': {'instances': ['MEA2'],
                      'id': u'9f8f2af7-6407-4f79-a6fe-302c56172231'}},
            'placement_attr': {}}


def get_dummy_param():
    return {u'mea1': {'substitution_mappings': {u'VL1b8587afb-60': {
            'type': 'tosca.nodes.mec.VL', 'properties': {
                'network_name': u'net_mgmt',
                'vendor': 'apmec'}}, 'requirements': {
                    'virtualLink2': u'VL2b8587afb-60',
                    'virtualLink1': u'VL1b8587afb-60'}, u'VL2b8587afb-60': {
                        'type': 'tosca.nodes.mec.VL',
                        'properties': {'network_name': u'net0',
                            'vendor': 'apmec'}}}},
            u'mesd': {u'vl2_name': u'net0', u'vl1_name': u'net_mgmt'}}


def get_dummy_create_workflow():
    return {'std.create_mea_dummy': {'input': ['mea'],
                'tasks': {
                    'wait_mea_active_MEA2': {
                        'action': 'apmec.show_mea mea=<% $.mea_id_MEA2 %>',
                        'retry': {'count': 10, 'delay': 10,
                            'continue-on': '<% $.status_MEA2 = '
                                           '"PENDING_CREATE" %>',
                            'break-on': '<% $.status_MEA2 = "ERROR" %>'},
                        'publish': {
                            'status_MEA2': '<% task(wait_mea_active_MEA2).'
                                           'result.mea.status %>',
                            'mgmt_url_MEA2': ' <% task(wait_mea_active_MEA2).'
                                             'result.mea.mgmt_url %>'},
                        'on-success': [{
                            'delete_mea_MEA2': '<% $.status_MEA2='
                                               '"ERROR" %>'}]},
                    'create_mea_MEA2': {
                        'action': 'apmec.create_mea body=<% $.mea.MEA2 %>',
                        'input': {'body': '<% $.mea.MEA2 %>'},
                        'publish': {
                            'status_MEA2': '<% task(create_mea_MEA2).'
                                           'result.mea.status %>',
                            'vim_id_MEA2': '<% task(create_mea_MEA2).'
                                           'result.mea.vim_id %>',
                            'mgmt_url_MEA2': '<% task(create_mea_MEA2).'
                                             'result.mea.mgmt_url %>',
                            'mea_id_MEA2': '<% task(create_mea_MEA2)'
                                           '.result.mea.id %>'},
                            'on-success': ['wait_mea_active_MEA2']},
                    'create_mea_MEA1': {
                        'action': 'apmec.create_mea body=<% $.mea.MEA1 %>',
                        'input': {'body': '<% $.mea.MEA1 %>'},
                        'publish': {
                            'status_MEA1': '<% task(create_mea_MEA1).'
                                           'result.mea.status %>',
                            'mea_id_MEA1': '<% task(create_mea_MEA1).'
                                           'result.mea.id %>',
                            'mgmt_url_MEA1': '<% task(create_mea_MEA1).'
                                             'result.mea.mgmt_url %>',
                            'vim_id_MEA1': '<% task(create_mea_MEA1).'
                                           'result.mea.vim_id %>'},
                        'on-success': ['wait_mea_active_MEA1']},
                    'wait_mea_active_MEA1': {
                        'action': 'apmec.show_mea mea=<% $.mea_id_MEA1 %>',
                        'retry': {'count': 10, 'delay': 10,
                            'continue-on': '<% $.status_MEA1 = "PENDING_'
                                           'CREATE" %>',
                            'break-on': '<% $.status_MEA1 = "ERROR" %>'},
                        'publish': {
                            'status_MEA1': '<% task(wait_mea_active_MEA1).'
                                           'result.mea.status %>',
                            'mgmt_url_MEA1': ' <% task(wait_mea_active_MEA1).'
                                             'result.mea.mgmt_url %>'},
                        'on-success': [{'delete_mea_MEA1': '<% $.status_MEA1='
                                                           '"ERROR" %>'}]},
                    'delete_mea_MEA1': {'action': 'apmec.delete_mea mea=<% '
                                                  '$.mea_id_MEA1%>'},
                    'delete_mea_MEA2': {'action': 'apmec.delete_mea mea=<% '
                                                  '$.mea_id_MEA2%>'}},
                'type': 'direct', 'output': {
                    'status_MEA1': '<% $.status_MEA1 %>',
                    'status_MEA2': '<% $.status_MEA2 %>',
                    'mgmt_url_MEA2': '<% $.mgmt_url_MEA2 %>',
                    'mgmt_url_MEA1': '<% $.mgmt_url_MEA1 %>',
                    'vim_id_MEA2': '<% $.vim_id_MEA2 %>',
                    'mea_id_MEA1': '<% $.mea_id_MEA1 %>',
                    'mea_id_MEA2': '<% $.mea_id_MEA2 %>',
                    'vim_id_MEA1': '<% $.vim_id_MEA1 %>'}},
            'version': '2.0'}


def dummy_delete_mes_obj():
    return {'mea_ids': u"{'MEA1': '5de5eca6-3e21-4bbd-a9d7-86458de75f0c'}"}


def get_dummy_delete_workflow():
    return {'version': '2.0',
            'std.delete_mea_dummy': {'input': ['mea_id_MEA1'],
                'tasks': {'delete_mea_MEA1': {
                    'action': 'apmec.delete_mea mea=<% $.mea_id_MEA1%>'}},
                'type': 'direct'}}


class FakeMistral(object):
    def __init__(self):
        pass


class FakeMEOPlugin(object):

    def __init__(self, context, client, resource, action):
        self.context = context
        self.client = client
        self.wg = workflow_generator.WorkflowGenerator(resource, action)

    def prepare_workflow(self, **kwargs):
        self.wg.task(**kwargs)


class TestWorkflowGenerator(base.TestCase):
    def setUp(self):
        super(TestWorkflowGenerator, self).setUp()
        self.mistral_client = FakeMistral()

    def test_prepare_workflow_create(self):
        fPlugin = FakeMEOPlugin(context, self.mistral_client,
                                 resource='mea', action='create')
        fPlugin.prepare_workflow(mes=get_dummy_mes(), params=get_dummy_param())
        wf_def_values = [fPlugin.wg.definition[k] for
            k in fPlugin.wg.definition]
        self.assertIn(get_dummy_create_workflow()['std.create_mea_dummy'],
                      wf_def_values)
        self.assertEqual(get_dummy_create_workflow()['version'],
                         fPlugin.wg.definition['version'])

    def test_prepare_workflow_delete(self):
        fPlugin = FakeMEOPlugin(context, self.mistral_client,
                                 resource='mea', action='delete')
        fPlugin.prepare_workflow(mes=dummy_delete_mes_obj())
        wf_def_values = [fPlugin.wg.definition[k] for
            k in fPlugin.wg.definition]
        self.assertIn(get_dummy_delete_workflow()['std.delete_mea_dummy'],
                      wf_def_values)
        self.assertEqual(get_dummy_delete_workflow()['version'],
                         fPlugin.wg.definition['version'])
