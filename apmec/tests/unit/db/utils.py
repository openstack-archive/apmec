# Copyright 2015 Brocade Communications System, Inc.
# All Rights Reserved.
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

import codecs
from datetime import datetime
import os
import yaml


DUMMY_mes_2_NAME = 'dummy_mes_2'


def _get_template(name):
    filename = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../mem/infra_drivers/openstack/data/", name)
    f = codecs.open(filename, encoding='utf-8', errors='strict')
    return f.read()

tosca_mead_openwrt = _get_template('test_tosca_openwrt.yaml')
config_data = _get_template('config_data.yaml')
update_config_data = _get_template('update_config_data.yaml')
mead_scale_tosca_template = _get_template('tosca_scale.yaml')
mead_alarm_respawn_tosca_template = _get_template(
    'test_tosca_mead_alarm_respawn.yaml')
mead_alarm_scale_tosca_template = _get_template(
    'test_tosca_mead_alarm_scale.yaml')
mead_alarm_multi_actions_tosca_template = _get_template(
    'test_tosca_mead_alarm_multi_actions.yaml')
mesd_tosca_template = yaml.safe_load(_get_template('tosca_mesd_template.yaml'))


def get_dummy_mead_obj():
    return {u'mead': {u'service_types': [{u'service_type': u'mead'}],
                      'name': 'dummy_mead',
                      'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                      u'attributes': {u'mead': yaml.safe_load(
                          tosca_mead_openwrt)},
                      'description': 'dummy_mead_description',
                      'template_source': 'onboarded',
            u'auth': {u'tenantName': u'admin', u'passwordCredentials': {
                u'username': u'admin', u'password': u'devstack'}}}}


def get_dummy_mead_obj_inline():
    return {u'mead': {u'service_types': [{u'service_type': u'mead'}],
                      'name': 'tmpl-koeak4tqgoqo8cr4-dummy_inline_mea',
                      'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                      u'attributes': {u'mead': yaml.safe_load(
                          tosca_mead_openwrt)},
                      'template_source': 'inline',
            u'auth': {u'tenantName': u'admin', u'passwordCredentials': {
                u'username': u'admin', u'password': u'devstack'}}}}


def get_dummy_inline_mea_obj():
    return {'mea': {'description': 'dummy_inline_mea_description',
                    'mead_template': yaml.safe_load(tosca_mead_openwrt),
                    'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                    'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                    'name': 'dummy_inline_mea',
                    'attributes': {},
                    'mead_id': None}}


def get_dummy_mea_obj():
    return {'mea': {'description': 'dummy_mea_description',
                    'mead_id': u'eb094833-995e-49f0-a047-dfb56aaf7c4e',
                    'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                    'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                    'name': 'dummy_mea',
                    'deleted_at': datetime.min,
                    'attributes': {},
                    'mead_template': None}}


def get_dummy_mea_config_obj():
    return {'mea': {u'attributes': {u'config': {'vdus': {'vdu1': {
        'config': {'firewall': 'dummy_firewall_values'}}}}}}}


def get_dummy_device_obj():
    return {'status': 'PENDING_CREATE', 'instance_id': None, 'name':
        u'test_openwrt', 'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
        'mead_id': u'eb094833-995e-49f0-a047-dfb56aaf7c4e',
        'mead': {
            'service_types': [{'service_type': u'mead',
            'id': u'4a4c2d44-8a52-4895-9a75-9d1c76c3e738'}],
            'description': u'OpenWRT with services',
            'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
            'mgmt_driver': u'openwrt',
            'attributes': {u'mead': tosca_mead_openwrt},
            'id': u'fb048660-dc1b-4f0f-bd89-b023666650ec',
            'name': u'openwrt_services'},
        'mgmt_url': None, 'service_context': [],
        'attributes': {u'param_values': u''},
        'id': 'eb84260e-5ff7-4332-b032-50a14d6c1123',
        'description': u'OpenWRT with services'}


def get_dummy_mea_config_attr():
    return {'status': 'PENDING_CREATE', 'instance_id': None, 'name':
        u'test_openwrt', 'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
        'mead_id': u'eb094833-995e-49f0-a047-dfb56aaf7c4e',
        'mead': {'service_types': [{'service_type': u'mead',
            'id': u'4a4c2d44-8a52-4895-9a75-9d1c76c3e738'}],
            'description': u'OpenWRT with services',
            'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
            'mgmt_driver': u'openwrt',
            'attributes': {u'mead': tosca_mead_openwrt},
            'id': u'fb048660-dc1b-4f0f-bd89-b023666650ec', 'name':
            u'openwrt_services'}, 'mgmt_url': None, 'service_context': [],
            'attributes': {u'config': config_data},
            'id': 'eb84260e-5ff7-4332-b032-50a14d6c1123',
            'description': u'OpenWRT with services'}


def get_dummy_mea_update_config():
    return {'mea': {'attributes': {'config': update_config_data}}}


def get_vim_obj():
    return {'vim': {'type': 'openstack', 'auth_url':
                    'http://localhost:5000', 'vim_project': {'name':
                    'test_project'}, 'auth_cred': {'username': 'test_user',
                                                   'password':
                                                       'test_password'},
                            'name': 'VIM0',
                    'tenant_id': 'test-project'}}


def get_vim_auth_obj():
    return {'username': 'test_user',
            'password': 'test_password',
            'project_id': None,
            'project_name': 'test_project',
            'auth_url': 'http://localhost:5000/v3',
            'user_domain_name': 'default',
            'project_domain_name': 'default'}

def get_dummy_mesd_obj():
    return {'mesd': {'description': 'dummy_mesd_description',
                    'name': 'dummy_MESD',
                    'tenant_id': u'8819a1542a5948b68f94d4be0fd50496',
                    'attributes': {u'mesd': mesd_tosca_template},
                    'template_source': 'onboarded'}}


def get_dummy_mesd_obj_inline():
    return {'mesd': {'description': 'dummy_mesd_description_inline',
                    'name': 'dummy_MESD_inline',
                    'tenant_id': u'8819a1542a5948b68f94d4be0fd50496',
                    'attributes': {u'mesd': mesd_tosca_template},
                    'template_source': 'inline'}}


def get_dummy_mes_obj():
    return {'mes': {'description': 'dummy_mes_description',
                   'id': u'ba6bf017-f6f7-45f1-a280-57b073bf78ea',
                   'mesd_id': u'eb094833-995e-49f0-a047-dfb56aaf7c4e',
                   'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                   'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                   'name': 'dummy_mes',
                   'attributes': {
                       'param_values': {'mesd': {'vl1_name': 'net_mgmt',
                                                'vl2_name': 'net0'}}}}}


def get_dummy_mes_obj_inline():
    return {'mes': {'description': 'dummy_mes_description_inline',
                   'id': u'ff35e3f0-0a11-4071-bce6-279fdf1c8bf9',
                   'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                   'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                   'name': 'dummy_mes_inline',
                   'attributes': {
                       'param_values': {'mesd': {'vl1_name': 'net_mgmt',
                                                'vl2_name': 'net0'}}},
                   'mesd_template': mesd_tosca_template}}


def get_dummy_mes_obj_2():
    return {'mes': {'description': 'dummy_mes_description',
                   'id': u'ba6bf017-f6f7-45f1-a280-57b073bf78ea',
                   'mesd_id': u'eb094833-995e-49f0-a047-dfb56aaf7c4e',
                   'vim_id': u'6261579e-d6f3-49ad-8bc3-a9cb974778ff',
                   'tenant_id': u'ad7ebc56538745a08ef7c5e97f8bd437',
                   'name': DUMMY_mes_2_NAME,
                   'attributes': {
                       'param_values': {'mesd': {'vl1_name': 'net_mgmt',
                                                'vl2_name': 'net0'}}}}}
