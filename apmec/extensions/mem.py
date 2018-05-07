# Copyright 2015 Intel Corporation..
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

from oslo_log import log as logging
import six

from apmec.api import extensions
from apmec.api.v1 import attributes as attr
from apmec.api.v1 import base
from apmec.api.v1 import resource_helper
from apmec.common import exceptions
from apmec import manager
from apmec.plugins.common import constants
from apmec.services import service_base


LOG = logging.getLogger(__name__)


class MultipleMGMTDriversSpecified(exceptions.InvalidInput):
    message = _('More than one MGMT Driver per mead is not supported')


class ServiceTypesNotSpecified(exceptions.InvalidInput):
    message = _('service types are not specified')


class MEADInUse(exceptions.InUse):
    message = _('MEAD %(mead_id)s is still in use')


class MEAInUse(exceptions.InUse):
    message = _('MEA %(mea_id)s is still in use')


class InvalidInfraDriver(exceptions.InvalidInput):
    message = _('VIM type %(vim_name)s is not supported as an infra driver ')


class InvalidServiceType(exceptions.InvalidInput):
    message = _('invalid service type %(service_type)s')


class MEACreateFailed(exceptions.ApmecException):
    message = _('creating MEA based on %(mead_id)s failed')


class MEACreateWaitFailed(exceptions.ApmecException):
    message = _('%(reason)s')


class MEAScaleWaitFailed(exceptions.ApmecException):
    message = _('%(reason)s')


class MEADeleteWaitFailed(exceptions.ApmecException):
    message = _('%(reason)s')


class MEADNotFound(exceptions.NotFound):
    message = _('MEAD %(mead_id)s could not be found')


class ServiceTypeNotFound(exceptions.NotFound):
    message = _('service type %(service_type_id)s could not be found')


class MEANotFound(exceptions.NotFound):
    message = _('MEA %(mea_id)s could not be found')


class ParamYAMLNotWellFormed(exceptions.InvalidInput):
    message = _("Parameter YAML not well formed - %(error_msg_details)s")


class ToscaParserFailed(exceptions.InvalidInput):
    message = _("tosca-parser failed: - %(error_msg_details)s")


class HeatTranslatorFailed(exceptions.InvalidInput):
    message = _("heat-translator failed: - %(error_msg_details)s")


class HeatClientException(exceptions.ApmecException):
    message = _("%(msg)s")


class UserDataFormatNotFound(exceptions.NotFound):
    message = _("user_data and/or user_data_format not provided")


class IPAddrInvalidInput(exceptions.InvalidInput):
    message = _("IP Address input values should be in a list format")


class HugePageSizeInvalidInput(exceptions.InvalidInput):
    message = _("Value specified for mem_page_size is invalid:"
                "%(error_msg_details)s. The valid values are 'small', 'large',"
                "'any' or an integer value in MB")


class CpuAllocationInvalidKeys(exceptions.InvalidInput):
    message = _("Invalid keys specified in MEAD - %(error_msg_details)s."
                "Supported keys are: %(valid_keys)s")


class NumaNodesInvalidKeys(exceptions.InvalidInput):
    message = _("Invalid keys specified in MEAD - %(error_msg_details)s."
                "Supported keys are: %(valid_keys)s")


class FilePathMissing(exceptions.InvalidInput):
    message = _("'file' attribute is missing for "
                "tosca.artifacts.Deployment.Image.VM artifact type")


class InfraDriverUnreachable(exceptions.ServiceUnavailable):
    message = _("Could not retrieve MEA resource IDs and"
                " types. Please check %(service)s status.")


class MEAInactive(exceptions.InvalidInput):
    message = _("MEA %(mea_id)s is not in Active state %(message)s")


class MetadataNotMatched(exceptions.InvalidInput):
    message = _("Metadata for alarm policy is not matched")


class InvalidSubstitutionMapping(exceptions.InvalidInput):
    message = _("Input for substitution mapping requirements are not"
                " valid for %(requirement)s. They must be in the form"
                " of list with two entries")


class SMRequirementMissing(exceptions.InvalidInput):
    message = _("All the requirements for substitution_mappings are not"
                " provided. Missing requirement for %(requirement)s")


class InvalidParamsForSM(exceptions.InvalidInput):
    message = _("Please provide parameters for substitution mappings")


def _validate_service_type_list(data, valid_values=None):
    if not isinstance(data, list):
        msg = _("invalid data format for service list: '%s'") % data
        LOG.debug(msg)
        return msg
    if not data:
        msg = _("empty list is not allowed for service list. '%s'") % data
        LOG.debug(msg)
        return msg
    key_specs = {
        'service_type': {
            'type:string': None,
        }
    }
    for service in data:
        msg = attr._validate_dict(service, key_specs)
        if msg:
            LOG.debug(msg)
            return msg


attr.validators['type:service_type_list'] = _validate_service_type_list


RESOURCE_ATTRIBUTE_MAP = {

    'meads': {
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
        'service_types': {
            'allow_post': True,
            'allow_put': False,
            'convert_to': attr.convert_to_list,
            'validate': {'type:service_type_list': None},
            'is_visible': True,
            'default': attr.ATTR_NOT_SPECIFIED,
        },
        'attributes': {
            'allow_post': True,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': None,
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
        'template_source': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
            'default': 'onboarded'
        },
    },

    'meas': {
        'id': {
            'allow_post': False,
            'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True,
            'primary_key': True
        },
        'tenant_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'required_by_policy': True,
            'is_visible': True
        },
        'mead_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:uuid': None},
            'is_visible': True,
            'default': None
        },
        'vim_id': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True,
            'default': '',
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
        'instance_id': {
            'allow_post': False,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True,
        },
        'mgmt_url': {
            'allow_post': False,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True,
        },
        'attributes': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:dict_or_none': None},
            'is_visible': True,
            'default': {},
        },
        'placement_attr': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:dict_or_none': None},
            'is_visible': True,
            'default': {},
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
        'mead_template': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:dict_or_none': None},
            'is_visible': True,
            'default': None,
        },
    },
}


SUB_RESOURCE_ATTRIBUTE_MAP = {
    'actions': {
        'parent': {
            'collection_name': 'meas',
            'member_name': 'mea'
        },
        'members': {
            'scale': {
                'parameters': {
                    'policy': {
                        'allow_post': True,
                        'allow_put': False,
                        'is_visible': True,
                        'validate': {'type:string': None}
                    },
                    'type': {
                        'allow_post': True,
                        'allow_put': False,
                        'is_visible': True,
                        'validate': {'type:string': None}
                    },
                    'tenant_id': {
                        'allow_post': True,
                        'allow_put': False,
                        'validate': {'type:string': None},
                        'required_by_policy': False,
                        'is_visible': False
                    },
                }
            },
        }
    },
    'triggers': {
        'parent': {
            'collection_name': 'meas',
            'member_name': 'mea'
        },
        'members': {
            'trigger': {
                'parameters': {
                    'policy_name': {
                        'allow_post': True,
                        'allow_put': False,
                        'is_visible': True,
                        'validate': {'type:string': None}
                    },
                    'action_name': {
                        'allow_post': True,
                        'allow_put': False,
                        'is_visible': True,
                        'validate': {'type:string': None}
                    },
                    'params': {
                        'allow_post': True,
                        'allow_put': False,
                        'is_visible': True,
                        'validate': {'type:dict_or_none': None}
                    },
                    'tenant_id': {
                        'allow_post': True,
                        'allow_put': False,
                        'validate': {'type:string': None},
                        'required_by_policy': False,
                        'is_visible': False
                    }
                }
            },
        }
    },
    'resources': {
        'parent': {
            'collection_name': 'meas',
            'member_name': 'mea'
        },
        'members': {
            'resource': {
                'parameters': {
                    'name': {
                        'allow_post': False,
                        'allow_put': False,
                        'is_visible': True,
                    },
                    'type': {
                        'allow_post': False,
                        'allow_put': False,
                        'is_visible': True,
                    },
                    'id': {
                        'allow_post': False,
                        'allow_put': False,
                        'is_visible': True,
                    },
                }
            }
        }
    }
}


class Mem(extensions.ExtensionDescriptor):
    @classmethod
    def get_name(cls):
        return 'MEA Manager'

    @classmethod
    def get_alias(cls):
        return 'MEM'

    @classmethod
    def get_description(cls):
        return "Extension for MEA Manager"

    @classmethod
    def get_namespace(cls):
        return 'http://wiki.openstack.org/Apmec'

    @classmethod
    def get_updated(cls):
        return "2013-11-19T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        special_mappings = {}
        plural_mappings = resource_helper.build_plural_mappings(
            special_mappings, RESOURCE_ATTRIBUTE_MAP)
        plural_mappings['service_types'] = 'service_type'
        attr.PLURALS.update(plural_mappings)
        resources = resource_helper.build_resource_info(
            plural_mappings, RESOURCE_ATTRIBUTE_MAP, constants.MEM,
            translate_name=True)
        plugin = manager.ApmecManager.get_service_plugins()[
            constants.MEM]
        for collection_name in SUB_RESOURCE_ATTRIBUTE_MAP:
            parent = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name]['parent']

            for resource_name in SUB_RESOURCE_ATTRIBUTE_MAP[
                    collection_name]['members']:
                params = SUB_RESOURCE_ATTRIBUTE_MAP[
                    collection_name]['members'][resource_name]['parameters']

                controller = base.create_resource(collection_name,
                                                  resource_name,
                                                  plugin, params,
                                                  allow_bulk=True,
                                                  parent=parent)

                resource = extensions.ResourceExtension(
                    collection_name,
                    controller, parent,
                    attr_map=params)
                resources.append(resource)
        return resources

    @classmethod
    def get_plugin_interface(cls):
        return MEMPluginBase

    def update_attributes_map(self, attributes):
        super(Mem, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        version_map = {'1.0': RESOURCE_ATTRIBUTE_MAP}
        return version_map.get(version, {})


@six.add_metaclass(abc.ABCMeta)
class MEMPluginBase(service_base.MECPluginBase):
    def get_plugin_name(self):
        return constants.MEM

    def get_plugin_type(self):
        return constants.MEM

    def get_plugin_description(self):
        return 'Apmec MEA Manager plugin'

    @abc.abstractmethod
    def create_mead(self, context, mead):
        pass

    @abc.abstractmethod
    def delete_mead(self, context, mead_id):
        pass

    @abc.abstractmethod
    def get_mead(self, context, mead_id, fields=None):
        pass

    @abc.abstractmethod
    def get_meads(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_meas(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_mea(self, context, mea_id, fields=None):
        pass

    @abc.abstractmethod
    def get_mea_resources(self, context, mea_id, fields=None, filters=None):
        pass

    @abc.abstractmethod
    def create_mea(self, context, mea):
        pass

    @abc.abstractmethod
    def update_mea(
            self, context, mea_id, mea):
        pass

    @abc.abstractmethod
    def delete_mea(self, context, mea_id):
        pass

    @abc.abstractmethod
    def create_mea_scale(
            self, context, mea_id, scale):
        pass

    @abc.abstractmethod
    def create_mea_trigger(
            self, context, mea_id, trigger):
        pass
