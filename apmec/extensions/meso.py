# Copyright 2016 Brocade Communications Systems Inc
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

import abc

import six

from apmec._i18n import _
from apmec.api import extensions
from apmec.api.v1 import attributes as attr
from apmec.api.v1 import resource_helper
from apmec.common import exceptions
from apmec.plugins.common import constants
from apmec.services import service_base


class MESDInUse(exceptions.InUse):
    message = _('MESD %(mesd_id)s is still in use')


class MESInUse(exceptions.InUse):
    message = _('MES %(mes_id)s is still in use')


class NoTasksException(exceptions.ApmecException):
    message = _('No tasks to run for %(action)s on %(resource)s')


class MESDNotFound(exceptions.NotFound):
    message = _('MESD %(mesd_id)s could not be found')


class MESNotFound(exceptions.NotFound):
    message = _('MES %(mes_id)s could not be found')


class ToscaParserFailed(exceptions.InvalidInput):
    message = _("tosca-parser failed: - %(error_msg_details)s")


class NSDNotFound(exceptions.NotFound):
    message = _('NSD template(s) not existed for MESD %(mesd_name)')


class VNFFGDNotFound(exceptions.NotFound):
    message = _('VNFFGD template(s) not existed for MESD %(mesd_name)')


class MECDriverNotfound(exceptions.NotFound):
    message = _('MEC driver not specified for the MESD %(mesd_name)')


class NFVDriverNotFound(exceptions.NotFound):
    message = _('NFV driver is not specified for the MESD %(mesd_name)')


RESOURCE_ATTRIBUTE_MAP = {
    'mesds': {
        'id': {
            'allow_post': False,
            'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True,
            'primary_key': True,
        },
        'tenant_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'required_by_policy': True,
            'is_visible': True,
        },
        'name': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True,
        },
        'description': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True,
            'default': '',
        },
        'mesd_mapping': {
            'allow_post': False,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': '',
        },
        'created_at': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
        },
        'updated_at': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
        },
        'attributes': {
            'allow_post': True,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': None,
        },
        'template_source': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
            'default': 'onboarded'
        },

    },

    'mess': {
        'id': {
            'allow_post': False,
            'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True,
            'primary_key': True,
        },
        'tenant_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'required_by_policy': True,
            'is_visible': True,
        },
        'name': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True,
        },
        'description': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:string': None},
            'is_visible': True,
            'default': '',
        },
        'created_at': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
        },
        'updated_at': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
        },
        'mes_mapping': {
            'allow_post': False,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': '',
        },
        'reused': {
            'allow_post': False,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': '',
        },
        'mesd_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True,
            'default': None,
        },
        'vim_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True,
            'default': '',
        },
        'status': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
        },
        'error_reason': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
        },
        'attributes': {
            'allow_post': True,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': None,
        },
        'mesd_template': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': None,
        },
    },

}


class Meso(extensions.ExtensionDescriptor):
    @classmethod
    def get_name(cls):
        return 'MEC Service Orchestrator'

    @classmethod
    def get_alias(cls):
        return 'MESO'

    @classmethod
    def get_description(cls):
        return "Extension for MEC Service Orchestrator"

    @classmethod
    def get_namespace(cls):
        return 'http://wiki.openstack.org/Apmec'

    @classmethod
    def get_updated(cls):
        return "2015-12-21T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        special_mappings = {}
        plural_mappings = resource_helper.build_plural_mappings(
            special_mappings, RESOURCE_ATTRIBUTE_MAP)
        attr.PLURALS.update(plural_mappings)
        return resource_helper.build_resource_info(
            plural_mappings, RESOURCE_ATTRIBUTE_MAP, constants.MESO,
            translate_name=True)

    @classmethod
    def get_plugin_interface(cls):
        return MESOPluginBase

    def update_attributes_map(self, attributes):
        super(Meso, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        version_map = {'1.0': RESOURCE_ATTRIBUTE_MAP}
        return version_map.get(version, {})


@six.add_metaclass(abc.ABCMeta)
class MESOPluginBase(service_base.MECPluginBase):
    def get_plugin_name(self):
        return constants.MESO

    def get_plugin_type(self):
        return constants.MESO

    def get_plugin_description(self):
        return 'Apmec MEC service Orchestrator plugin'

    @abc.abstractmethod
    def create_mesd(self, context, mesd):
        pass

    @abc.abstractmethod
    def delete_mesd(self, context, mesd_id):
        pass

    @abc.abstractmethod
    def get_mesd(self, context, mesd_id, fields=None):
        pass

    @abc.abstractmethod
    def get_mesds(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_mes(self, context, mes):
        pass

    @abc.abstractmethod
    def get_mess(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_mes(self, context, mes_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_mes(self, context, mes_id):
        pass

    @abc.abstractmethod
    def update_mes(self, context, mes_id, mes):
        pass
