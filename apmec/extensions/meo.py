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


class VimUnauthorizedException(exceptions.ApmecException):
    message = _("%(message)s")


class VimConnectionException(exceptions.ApmecException):
    message = _("%(message)s")


class VimInUseException(exceptions.ApmecException):
    message = _("VIM %(vim_id)s is still in use by MEA")


class VimDefaultNotDefined(exceptions.ApmecException):
    message = _("Default VIM is not defined.")


class VimDefaultDuplicateException(exceptions.ApmecException):
    message = _("Default VIM already exists %(vim_id)s.")


class VimNotFoundException(exceptions.ApmecException):
    message = _("Specified VIM id %(vim_id)s is invalid. Please verify and "
                "pass a valid VIM id")


class VimRegionNotFoundException(exceptions.ApmecException):
    message = _("Unknown VIM region name %(region_name)s")


class VimKeyNotFoundException(exceptions.ApmecException):
    message = _("Unable to find key file for VIM %(vim_id)s")


class VimUnsupportedResourceTypeException(exceptions.ApmecException):
    message = _("Resource type %(type)s is unsupported by VIM")


class VimGetResourceException(exceptions.ApmecException):
    message = _("Error while trying to issue %(cmd)s to find resource type "
                "%(type)s by resource name %(name)s")


class VimGetResourceNameNotUnique(exceptions.ApmecException):
    message = _("Getting resource id from VIM with resource name %(name)s "
                "by %(cmd)s returns more than one")


class VimGetResourceNotFoundException(exceptions.ApmecException):
    message = _("Getting resource id from VIM with resource name %(name)s "
                "by %(cmd)s returns nothing")


class VimFromMeaNotFoundException(exceptions.NotFound):
    message = _('VIM from MEA %(mea_id)s could not be found')


class ToscaParserFailed(exceptions.InvalidInput):
    message = _("tosca-parser failed: - %(error_msg_details)s")


class NfydInvalidTemplate(exceptions.InvalidInput):
    message = _("Invalid NFY template input: %(template)s")


class NfydDuplicateForwarderException(exceptions.InvalidInput):
    message = _("Invalid Forwarding Path contains duplicate forwarder not in "
                "order: %(forwarder)s")


class NfydDuplicateCPException(exceptions.InvalidInput):
    message = _("Invalid Forwarding Path contains duplicate connection point "
                ": %(cp)s")


class NfydCpNotFoundException(exceptions.NotFound):
    message = _("Specified CP %(cp_id)s could not be found in MEAD "
                "%(mead_name)s. Please check MEAD for correct Connection "
                "Point.")


class NfydCpNoForwardingException(exceptions.ApmecException):
    message = _("Specified CP %(cp_id)s in MEAD %(mead_name)s "
                "does not have forwarding capability, which is required to be "
                "included in forwarding path")


class NfydWrongEndpointNumber(exceptions.ApmecException):
    message = _("Specified number_of_endpoints %(number)s is not equal to "
                "the number of connection_point %(cps)s")


class NfyInvalidMappingException(exceptions.ApmecException):
    message = _("Matching MEA Instance for MEAD %(mead_name)s could not be "
                "found. Please create an instance of this MEAD before "
                "creating/updating NFY.")


class NfyParamValueFormatError(exceptions.ApmecException):
    message = _("Param values %(param_value)s is not in dict format.")


class NfyParamValueNotUsed(exceptions.ApmecException):
    message = _("Param input %(param_key)s not used.")


class NfyCpNotFoundException(exceptions.NotFound):
    message = _("Specified CP %(cp_id)s could not be found in MEA "
                "%(mea_id)s.")


class NfyMeaNotFoundException(exceptions.NotFound):
    message = _("Specified MEA instance %(mea_name)s in MEA Mapping could not "
                "be found")


class NfpAttributeNotFoundException(exceptions.NotFound):
    message = _('NFP attribute %(attribute)s could not be found')


class NfpNotFoundException(exceptions.NotFound):
    message = _('NFP %(nfp_id)s could not be found')


class NfpInUse(exceptions.InUse):
    message = _('NFP %(nfp_id)s is still in use')


class NfpPolicyCriteriaError(exceptions.PolicyCheckError):
    message = _('%(error)s in policy')


class NfpPolicyNotFoundException(exceptions.NotFound):
    message = _('Policy not found in NFP %(nfp)s')


class NfpPolicyTypeError(exceptions.PolicyCheckError):
    message = _('Unsupported Policy Type: %(type)s')


class NfpForwarderNotFoundException(exceptions.NotFound):
    message = _('MEAD Forwarder %(mead)s not found in MEA Mapping %(mapping)s')


class NfpRequirementsException(exceptions.ApmecException):
    message = _('MEAD Forwarder %(mead)s specified more than twice in '
                'requirements path')


class SfcInUse(exceptions.InUse):
    message = _('SFC %(sfc_id)s is still in use')


class SfcNotFoundException(exceptions.NotFound):
    message = _('Service Function Chain %(sfc_id)s could not be found')


class ClassifierInUse(exceptions.InUse):
    message = _('Classifier %(classifier_id)s is still in use')


class ClassifierNotFoundException(exceptions.NotFound):
    message = _('Classifier %(classifier_id)s could not be found')


class MESDInUse(exceptions.InUse):
    message = _('MESD %(mesd_id)s is still in use')


class MESInUse(exceptions.InUse):
    message = _('MES %(mes_id)s is still in use')


class NoTasksException(exceptions.ApmecException):
    message = _('No tasks to run for %(action)s on %(resource)s')


RESOURCE_ATTRIBUTE_MAP = {

    'vims': {
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
            'is_visible': True
        },
        'type': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True
        },
        'auth_url': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True
        },
        'auth_cred': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
        },
        'vim_project': {
            'allow_post': True,
            'allow_put': True,
            'validate': {'type:dict_or_nodata': None},
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
        'status': {
            'allow_post': False,
            'allow_put': False,
            'validate': {'type:string': None},
            'is_visible': True,
        },
        'placement_attr': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': True,
            'default': None,
        },
        'shared': {
            'allow_post': False,
            'allow_put': False,
            'is_visible': False,
            'convert_to': attr.convert_to_boolean,
            'required_by_policy': True
        },
        'is_default': {
            'allow_post': True,
            'allow_put': True,
            'is_visible': True,
            'default': False
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
    },
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
        'mea_ids': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:string': None},
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
        'mgmt_urls': {
            'allow_post': False,
            'allow_put': False,
            'convert_to': attr.convert_none_to_empty_dict,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
        },
        'mesd_template': {
            'allow_post': True,
            'allow_put': False,
            'validate': {'type:dict_or_nodata': None},
            'is_visible': True,
            'default': None,
        },
    },

}


class Meo(extensions.ExtensionDescriptor):
    @classmethod
    def get_name(cls):
        return 'MEC Orchestrator'

    @classmethod
    def get_alias(cls):
        return 'MEO'

    @classmethod
    def get_description(cls):
        return "Extension for MEC Orchestrator"

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
            plural_mappings, RESOURCE_ATTRIBUTE_MAP, constants.MEO,
            translate_name=True)

    @classmethod
    def get_plugin_interface(cls):
        return MEOPluginBase

    def update_attributes_map(self, attributes):
        super(Meo, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        version_map = {'1.0': RESOURCE_ATTRIBUTE_MAP}
        return version_map.get(version, {})


@six.add_metaclass(abc.ABCMeta)
class MEOPluginBase(service_base.MECPluginBase):
    def get_plugin_name(self):
        return constants.MEO

    def get_plugin_type(self):
        return constants.MEO

    def get_plugin_description(self):
        return 'Apmec MEC Orchestrator plugin'

    @abc.abstractmethod
    def create_vim(self, context, vim):
        pass

    @abc.abstractmethod
    def update_vim(self, context, vim_id, vim):
        pass

    @abc.abstractmethod
    def delete_vim(self, context, vim_id):
        pass

    @abc.abstractmethod
    def get_vim(self, context, vim_id, fields=None, mask_password=True):
        pass

    @abc.abstractmethod
    def get_vims(self, context, filters=None, fields=None):
        pass

    def get_vim_by_name(self, context, vim_name, fields=None,
                        mask_password=True):
        raise NotImplementedError()

    def get_default_vim(self, context):
        raise NotImplementedError()
