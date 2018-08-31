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

from keystoneauth1 import identity
from keystoneauth1 import session
from oslo_config import cfg
from oslo_log import log as logging

from apmec.meso.drivers.nfv_drivers import abstract_driver

from tackerclient.v1_0 import client as tacker_client

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Tacker_Driver(abstract_driver.NfvAbstractDriver):
    """Driver for NFV

    OpenStack driver handles interactions with local as well as
    remote OpenStack instances. The driver invokes keystone service for VIM
    authorization and validation. The driver is also responsible for
    discovering placement attributes such as regions, availability zones
    """

    def get_type(self):
        return 'tacker'

    def get_name(self):
        return 'OpenStack Tacker Driver'

    def get_description(self):
        return 'OpenStack Tacker Driver'

    def nsd_create(self, auth_attr, nsd_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.nsd_create(nsd_dict)

    def nsd_get_by_name(self, auth_attr, nsd_name):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.nsd_get_by_name(nsd_name)

    def nsd_get(self, auth_attr, nsd_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.nsd_get(nsd_id)

    def ns_create(self, auth_attr, ns_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_create(ns_dict)

    def ns_get_by_name(self, auth_attr, ns_name):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_get(ns_name)

    def ns_get(self, auth_attr, ns_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_get(ns_id)

    def ns_check(self, auth_attr, ns_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_check(ns_id)

    def ns_delete_by_name(self, auth_attr, ns_name):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_delete(ns_name)

    def ns_delete(self, auth_attr, ns_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_delete(ns_id)

    def ns_update(self, auth_attr, ns_id, ns_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_update(ns_id, ns_dict)

    def vnfd_create(self, auth_attr, vnfd_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnfd_create(vnfd_dict)

    def vnf_create(self, auth_attr, vnf_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnf_create(vnf_dict)

    def vnf_get(self, auth_attr, vnf_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnf_get(vnf_id)

    def vnfd_get(self, auth_attr, vnfd_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnfd_get(vnfd_id)

    def vnffgd_get_by_name(self, auth_attr, vnffgd_name):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffgd_get(vnffgd_name)

    def vnffgd_get(self, auth_attr, vnffgd_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffgd_get(vnffgd_id)

    def vnffg_create(self, auth_attr, vnffg_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffg_create(vnffg_dict)

    def vnffg_get_by_name(self, auth_attr, vnffg_name):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffg_get(vnffg_name)

    def vnffg_get(self, auth_attr, vnffg_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffg_get(vnffg_id)

    def vnffg_delete_by_name(self, auth_attr, vnffg_name):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffg_delete(vnffg_name)

    def vnffg_delete(self, auth_attr, vnffg_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffg_delete(vnffg_id)

    def vnffg_check(self, auth_attr, vnffg_id):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.vnffg_check(vnffg_id)

    def vnffg_update(self, auth_attr, vnffg_id, vnffg_dict):
        tacker_client = TackerClient(auth_attr)
        return tacker_client.ns_update(vnffg_id, vnffg_dict)


class TackerClient(object):
    """Tacker Client class for VNFM and NFVO negotiation"""

    def __init__(self, auth_attr):
        auth = identity.Password(**auth_attr)
        sess = session.Session(auth=auth)
        self.client = tacker_client.Client(session=sess)

    def nsd_create(self, nsd_dict):
        nsd_instance = self.client.create_nsd(body=nsd_dict)
        if nsd_instance:
            return nsd_instance['nsd']['id']
        else:
            return None

    def nsd_get_by_name(self, nsd_name):
        nsd_dict = self.client.list_nsds()
        nsd_list = nsd_dict['nsds']
        nsd_dict = None
        for nsd in nsd_list:
            if nsd['name'] == nsd_name:
                nsd_dict = nsd
        return nsd_dict

    def nsd_get(self, nsd_id):
        nsd_dict = self.client.show_nsd(nsd_id)
        return nsd_dict['nsd']

    def ns_create(self, ns_dict):
        ns_instance = self.client.create_ns(body=ns_dict)
        if ns_instance:
            return ns_instance['ns']['id']
        else:
            return None

    def ns_get_by_name(self, ns_name):
        ns_dict = self.client.list_nsds()
        ns_list = ns_dict['nss']
        ns_id = None
        for ns in ns_list:
            if ns['name'] == ns_name:
                ns_id = ns['id']
        return ns_id

    def ns_get(self, ns_id):
        ns_instance = self.client.show_ns(ns_id)
        return ns_instance['ns']

    def ns_delete_by_name(self, ns_name):
        ns_id = self.ns_get_by_name(ns_name)
        if ns_id:
            self.client.delete_ns(ns_id)

    def ns_check(self, ns_id):
        ns_dict = self.client.list_nss()
        ns_list = ns_dict['nss']
        check = False
        for ns in ns_list:
            if ns['id'] == ns_id:
                check = True
        return check

    def ns_delete(self, ns_id):
        return self.client.delete_ns(ns_id)

    def ns_update(self, ns_id, ns_dict):
        return self.client.update_ns(ns_id, ns_dict)

    def vnfd_create(self, vnfd_dict):
        vnfd_instance = self.client.create_vnfd(body=vnfd_dict)
        if vnfd_instance:
            return vnfd_instance['vnf']['id']
        else:
            return None

    def vnf_create(self, vnf_dict):
        vnf_instance = self.client.create_vnf(body=vnf_dict)
        if vnf_instance:
            return vnf_instance['vnf']['id']
        else:
            return None

    def vnf_get(self, vnf_id):
        vnf_instance = self.client.show_vnf(vnf_id)
        return vnf_instance['vnf']

    def vnfd_get(self, vnfd_id):
        vnfd_instance = self.client.show_vnfd(vnfd_id)
        return vnfd_instance['vnfd']

    def vnffgd_get_by_name(self, vnffgd_name):
        vnffgd_dict = self.client.list_vnffgds()
        vnffgd_list = vnffgd_dict['vnffgds']
        vnffgd_dict = None
        for vnffgd in vnffgd_list:
            if vnffgd['name'] == vnffgd_name:
                vnffgd_dict = vnffgd
        return vnffgd_dict

    def vnffgd_get(self, vnffgd_id):
        vnffgd_instance = self.client.show_vnffgd(vnffgd_id)
        return vnffgd_instance['vnffgd']

    def vnffg_create(self, vnffgd_dict):
        vnffg_instance = self.client.create_vnffg(body=vnffgd_dict)
        if vnffg_instance:
            return vnffg_instance['vnffg']['id']
        else:
            return None

    def vnffg_get_by_name(self, vnffg_name):
        vnffg_dict = self.client.list_vnffgs()
        vnffg_list = vnffg_dict['vnffgs']
        vnffg_id = None
        for vnffg in vnffg_list:
            if vnffg['name'] == vnffg_name:
                vnffg_id = vnffg['id']
        return vnffg_id

    def vnffg_get(self, vnffg_id):
        vnffg_instance = self.client.show_vnffg(vnffg_id)
        return vnffg_instance['vnffg']

    def vnffg_delete_by_name(self, vnffg_name):
        vnffg_id = self.vnffg_get_by_name(vnffg_name)
        if vnffg_id:
            self.client.delete_vnffg(vnffg_id)

    def vnffg_delete(self, vnffg_id):
        return self.client.delete_vnffg(vnffg_id)

    def vnffg_check(self, vnffg_id):
        vnffg_dict = self.client.list_vnffgs()
        vnffg_list = vnffg_dict['vnffgs']
        check = False
        for vnffg in vnffg_list:
            if vnffg['id'] == vnffg_id:
                check = True
        return check

    def vnffg_update(self, vnffg_id, vnffg_dict):
        return self.client.update_ns(vnffg_id, vnffg_dict)
