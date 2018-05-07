# Copyright 2016 Brocade Communications System, Inc.
# All Rights Reserved.
#
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

import copy
import os
import time
import yaml

from cryptography import fernet
import eventlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import strutils
from oslo_utils import uuidutils
from tempfile import mkstemp
from toscaparser.tosca_template import ToscaTemplate

from apmec._i18n import _
from apmec.common import driver_manager
from apmec.common import log
from apmec.common import utils
from apmec.db.meo import meo_db_plugin
from apmec.db.meo import mes_db
from apmec.extensions import common_services as cs
from apmec.extensions import meo
from apmec.keymgr import API as KEYMGR_API
from apmec import manager
from apmec.meo.workflows.vim_monitor import vim_monitor_utils
from apmec.plugins.common import constants
from apmec.mem import vim_client
from apmec.nfv.tacker_client import TackerClient as tackerclient

from apmec.catalogs.tosca import utils as toscautils
from toscaparser import tosca_template

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
MISTRAL_RETRIES = 30
MISTRAL_RETRY_WAIT = 6


def config_opts():
    return [('meo_vim', MeoPlugin.OPTS)]


class MeoPlugin(meo_db_plugin.MeoPluginDb, mes_db.MESPluginDb):
    """MEO reference plugin for MEO extension

    Implements the MEO extension and defines public facing APIs for VIM
    operations. MEO internally invokes the appropriate VIM driver in
    backend based on configured VIM types. Plugin also interacts with MEM
    extension for providing the specified VIM information
    """
    supported_extension_aliases = ['meo']

    OPTS = [
        cfg.ListOpt(
            'vim_drivers', default=['openstack'],
            help=_('VIM driver for launching MEAs')),
        cfg.IntOpt(
            'monitor_interval', default=30,
            help=_('Interval to check for VIM health')),
    ]
    cfg.CONF.register_opts(OPTS, 'meo_vim')

    def __init__(self):
        super(MeoPlugin, self).__init__()
        self._pool = eventlet.GreenPool()
        self._vim_drivers = driver_manager.DriverManager(
            'apmec.meo.vim.drivers',
            cfg.CONF.meo_vim.vim_drivers)
        self.vim_client = vim_client.VimClient()

    def get_auth_dict(self, context):
        auth = CONF.keystone_authtoken
        return {
            'auth_url': auth.auth_url + '/v3',
            'token': context.auth_token,
            'project_domain_name': auth.project_domain_name or context.domain,
            'project_name': context.tenant_name
        }

    def spawn_n(self, function, *args, **kwargs):
        self._pool.spawn_n(function, *args, **kwargs)

    @log.log
    def create_vim(self, context, vim):
        LOG.debug('Create vim called with parameters %s',
                  strutils.mask_password(vim))
        vim_obj = vim['vim']
        vim_type = vim_obj['type']
        vim_obj['id'] = uuidutils.generate_uuid()
        vim_obj['status'] = 'PENDING'
        try:
            self._vim_drivers.invoke(vim_type,
                                     'register_vim',
                                     context=context,
                                     vim_obj=vim_obj)
            res = super(MeoPlugin, self).create_vim(context, vim_obj)
        except Exception:
            with excutils.save_and_reraise_exception():
                self._vim_drivers.invoke(vim_type,
                                         'delete_vim_auth',
                                         context=context,
                                         vim_id=vim_obj['id'],
                                         auth=vim_obj['auth_cred'])

        try:
            self.monitor_vim(context, vim_obj)
        except Exception:
            LOG.warning("Failed to set up vim monitoring")
        return res

    def _get_vim(self, context, vim_id):
        if not self.is_vim_still_in_use(context, vim_id):
            return self.get_vim(context, vim_id, mask_password=False)

    @log.log
    def update_vim(self, context, vim_id, vim):
        vim_obj = self._get_vim(context, vim_id)
        old_vim_obj = copy.deepcopy(vim_obj)
        utils.deep_update(vim_obj, vim['vim'])
        vim_type = vim_obj['type']
        update_args = vim['vim']
        old_auth_need_delete = False
        new_auth_created = False
        try:
            # re-register the VIM only if there is a change in password.
            # auth_url of auth_cred is from vim object which
            # is not updatable. so no need to consider it
            if 'auth_cred' in update_args:
                auth_cred = update_args['auth_cred']
                if 'password' in auth_cred:
                    vim_obj['auth_cred']['password'] = auth_cred['password']
                    # Notice: vim_obj may be updated in vim driver's
                    self._vim_drivers.invoke(vim_type,
                                             'register_vim',
                                             context=context,
                                             vim_obj=vim_obj)
                    new_auth_created = True

                    # Check whether old vim's auth need to be deleted
                    old_key_type = old_vim_obj['auth_cred'].get('key_type')
                    if old_key_type == 'barbican_key':
                        old_auth_need_delete = True

            vim_obj = super(MeoPlugin, self).update_vim(
                context, vim_id, vim_obj)
            if old_auth_need_delete:
                try:
                    self._vim_drivers.invoke(vim_type,
                                             'delete_vim_auth',
                                             context=context,
                                             vim_id=old_vim_obj['id'],
                                             auth=old_vim_obj['auth_cred'])
                except Exception as ex:
                    LOG.warning("Fail to delete old auth for vim %s due to %s",
                                vim_id, ex)
            return vim_obj
        except Exception as ex:
            LOG.debug("Got exception when update_vim %s due to %s",
                      vim_id, ex)
            with excutils.save_and_reraise_exception():
                if new_auth_created:
                    # delete new-created vim auth, old auth is still used.
                    self._vim_drivers.invoke(vim_type,
                                             'delete_vim_auth',
                                             context=context,
                                             vim_id=vim_obj['id'],
                                             auth=vim_obj['auth_cred'])

    @log.log
    def delete_vim(self, context, vim_id):
        vim_obj = self._get_vim(context, vim_id)
        self._vim_drivers.invoke(vim_obj['type'],
                                 'deregister_vim',
                                 context=context,
                                 vim_obj=vim_obj)
        try:
            auth_dict = self.get_auth_dict(context)
            vim_monitor_utils.delete_vim_monitor(context, auth_dict, vim_obj)
        except Exception:
            LOG.exception("Failed to remove vim monitor")
        super(MeoPlugin, self).delete_vim(context, vim_id)

    @log.log
    def monitor_vim(self, context, vim_obj):
        auth_dict = self.get_auth_dict(context)
        vim_monitor_utils.monitor_vim(auth_dict, vim_obj)

    @log.log
    def validate_tosca(self, template):
        if "tosca_definitions_version" not in template:
            raise meo.ToscaParserFailed(
                error_msg_details='tosca_definitions_version missing in '
                                  'template'
            )

        LOG.debug('template yaml: %s', template)

        toscautils.updateimports(template)

        try:
            tosca_template.ToscaTemplate(
                a_file=False, yaml_dict_tpl=template)
        except Exception as e:
            LOG.exception("tosca-parser error: %s", str(e))
            raise meo.ToscaParserFailed(error_msg_details=str(e))

    def _get_vim_from_mea(self, context, mea_id):
        """Figures out VIM based on a MEA

        :param context: SQL Session Context
        :param mea_id: MEA ID
        :return: VIM or VIM properties if fields are provided
        """
        mem_plugin = manager.ApmecManager.get_service_plugins()['MEM']
        vim_id = mem_plugin.get_mea(context, mea_id, fields=['vim_id'])
        vim_obj = self.get_vim(context, vim_id['vim_id'], mask_password=False)
        if vim_obj is None:
            raise meo.VimFromMeaNotFoundException(mea_id=mea_id)
        self._build_vim_auth(context, vim_obj)
        return vim_obj

    def _build_vim_auth(self, context, vim_info):
        LOG.debug('VIM id is %s', vim_info['id'])
        vim_auth = vim_info['auth_cred']
        vim_auth['password'] = self._decode_vim_auth(context,
                                                     vim_info['id'],
                                                     vim_auth)
        vim_auth['auth_url'] = vim_info['auth_url']

        # These attributes are needless for authentication
        # from keystone, so we remove them.
        needless_attrs = ['key_type', 'secret_uuid']
        for attr in needless_attrs:
            if attr in vim_auth:
                vim_auth.pop(attr, None)
        return vim_auth

    def _decode_vim_auth(self, context, vim_id, auth):
        """Decode Vim credentials

        Decrypt VIM cred, get fernet Key from local_file_system or
        barbican.
        """
        cred = auth['password'].encode('utf-8')
        if auth.get('key_type') == 'barbican_key':
            keystone_conf = CONF.keystone_authtoken
            secret_uuid = auth['secret_uuid']
            keymgr_api = KEYMGR_API(keystone_conf.auth_url)
            secret_obj = keymgr_api.get(context, secret_uuid)
            vim_key = secret_obj.payload
        else:
            vim_key = self._find_vim_key(vim_id)

        f = fernet.Fernet(vim_key)
        if not f:
            LOG.warning('Unable to decode VIM auth')
            raise meo.VimNotFoundException(
                'Unable to decode VIM auth key')
        return f.decrypt(cred)

    @staticmethod
    def _find_vim_key(vim_id):
        key_file = os.path.join(CONF.vim_keys.openstack, vim_id)
        LOG.debug('Attempting to open key file for vim id %s', vim_id)
        with open(key_file, 'r') as f:
            return f.read()
        LOG.warning('VIM id invalid or key not found for  %s', vim_id)

    def _vim_resource_name_to_id(self, context, resource, name, mea_id):
        """Converts a VIM resource name to its ID

        :param resource: resource type to find (network, subnet, etc)
        :param name: name of the resource to find its ID
        :param mea_id: A MEA instance ID that is part of the chain to which
               the classifier will apply to
        :return: ID of the resource name
        """
        vim_obj = self._get_vim_from_mea(context, mea_id)
        driver_type = vim_obj['type']
        return self._vim_drivers.invoke(driver_type,
                                        'get_vim_resource_id',
                                        vim_obj=vim_obj,
                                        resource_type=resource,
                                        resource_name=name)

    @log.log
    def create_mesd(self, context, mesd):
        mesd_data = mesd['mesd']
        template = mesd_data['attributes'].get('mesd')
        if isinstance(template, dict):
            mesd_data['attributes']['mesd'] = yaml.safe_dump(
                template)
        LOG.debug('mesd %s', mesd_data)

        if 'template_source' in mesd_data:
            template_source = mesd_data.get('template_source')
        else:
            template_source = "onboarded"
        mesd['mesd']['template_source'] = template_source

        self._parse_template_input(context, mesd)
        return super(MeoPlugin, self).create_mesd(
            context, mesd)

    def _parse_template_input(self, context, mesd):
        mesd_dict = mesd['mesd']
        mesd_yaml = mesd_dict['attributes'].get('mesd')
        inner_mesd_dict = yaml.safe_load(mesd_yaml)
        mesd['meads'] = dict()
        LOG.debug('mesd_dict: %s', inner_mesd_dict)
        # From import we can deploy both NS and MEC Application
        nsd_imports = inner_mesd_dict['imports'].get('nsds')
        vnffg_imports = inner_mesd_dict['imports'].get('vnffgds')
        if nsd_imports:
            mesd_dict['attributes']['nsds'] = nsd_imports
        if vnffg_imports:
            mesd_dict['attributes']['vnffgds'] = vnffg_imports

        # Deploy MEC applications
        mem_plugin = manager.ApmecManager.get_service_plugins()['MEM']
        mead_imports = inner_mesd_dict['imports']['meads']
        inner_mesd_dict['imports'] = []
        new_files = []
        for mead_name in mead_imports:
            mead = mem_plugin.get_mead(context, mead_name)
            # Copy MEA types and MEA names
            sm_dict = yaml.safe_load(mead['attributes']['mead'])[
                'topology_template'][
                'substitution_mappings']
            mesd['meads'][sm_dict['node_type']] = mead['name']
            # Ugly Hack to validate the child templates
            # TODO(tbh): add support in tosca-parser to pass child
            # templates as dict
            fd, temp_path = mkstemp()
            with open(temp_path, 'w') as fp:
                fp.write(mead['attributes']['mead'])
            os.close(fd)
            new_files.append(temp_path)
            inner_mesd_dict['imports'].append(temp_path)
        # Prepend the apmec_defs.yaml import file with the full
        # path to the file
        toscautils.updateimports(inner_mesd_dict)

        try:
            ToscaTemplate(a_file=False,
                          yaml_dict_tpl=inner_mesd_dict)
        except Exception as e:
            LOG.exception("tosca-parser error: %s", str(e))
            raise meo.ToscaParserFailed(error_msg_details=str(e))
        finally:
            for file_path in new_files:
                os.remove(file_path)
            inner_mesd_dict['imports'] = mead_imports

        if ('description' not in mesd_dict or
                mesd_dict['description'] == ''):
            mesd_dict['description'] = inner_mesd_dict.get(
                'description', '')
        if (('name' not in mesd_dict or
                not len(mesd_dict['name'])) and
                'metadata' in inner_mesd_dict):
            mesd_dict['name'] = inner_mesd_dict['metadata'].get(
                'template_name', '')

        LOG.debug('mesd %s', mesd)

    def _get_mead_id(self, mead_name, onboarded_meads):
        for mead in onboarded_meads:
            if mead_name == mead['name']:
                return mead['id']

    @log.log
    def create_mes(self, context, mes):
        """Create MES and corresponding MEAs.

        :param mes: mes dict which contains mesd_id and attributes
        This method has 3 steps:
        step-1: substitute all get_input params to its corresponding values
        step-2: Build params dict for substitution mappings case through which
        MEAs will actually substitute their requirements.
        step-3: Create mistral workflow and execute the workflow
        """
        mes_info = mes['mes']
        name = mes_info['name']

        if mes_info.get('mesd_template'):
            mesd_name = utils.generate_resource_name(name, 'inline')
            mesd = {'mesd': {
                'attributes': {'mesd': mes_info['mesd_template']},
                'description': mes_info['description'],
                'name': mesd_name,
                'template_source': 'inline',
                'tenant_id': mes_info['tenant_id']}}
            mes_info['mesd_id'] = self.create_mesd(context, mesd).get('id')

        mesd = self.get_mesd(context, mes['mes']['mesd_id'])
        mesd_dict = yaml.safe_load(mesd['attributes']['mesd'])
        mem_plugin = manager.ApmecManager.get_service_plugins()['MEM']
        onboarded_meads = mem_plugin.get_meads(context, [])
        region_name = mes.setdefault('placement_attr', {}).get(
            'region_name', None)
        vim_res = self.vim_client.get_vim(context, mes['mes']['vim_id'],
                                          region_name)
        driver_type = vim_res['vim_type']
        if not mes['mes']['vim_id']:
            mes['mes']['vim_id'] = vim_res['vim_id']

        nsds = mesd['attributes'].get('nsds')
        if nsds:
            for nsd in nsds:
                vim_obj = self.get_vim(context, mes['mes']['vim_id'], mask_password=False)
                self._build_vim_auth(context, vim_obj)
                client = tackerclient(vim_obj['auth_cred'])
                ns_name = nsd + name
                nsd_instance = client.nsd_get(nsd)
                ns_arg = {'ns': {'nsd_id': nsd_instance, 'name': ns_name}}
                ns_instance = client.ns_create(ns_arg)

        vnffgds = mesd['attributes'].get('vnffgds')
        if vnffgds:
            for vnffgd in vnffgds:
                vim_obj = self.get_vim(context, mes['mes']['vim_id'], mask_password=False)
                self._build_vim_auth(context, vim_obj)
                client = tackerclient(vim_obj['auth_cred'])
                vnffgd_name = vnffgd + name
                vnffgd_instance = client.vnffgd_get(vnffgd)
                vnffg_arg = {'vnffg': {'vnffgd_id': vnffgd_instance, 'name': vnffgd_name}}
                time.sleep(300)
                vnffg_instance = client.vnffg_create(vnffg_arg)

        # Step-1
        param_values = mes['mes']['attributes'].get('param_values', {})
        if 'get_input' in str(mesd_dict):
            self._process_parameterized_input(mes['mes']['attributes'],
                                              mesd_dict)
        # Step-2
        meads = mesd['meads']
        # mead_dict is used while generating workflow
        mead_dict = dict()
        for node_name, node_val in \
                (mesd_dict['topology_template']['node_templates']).items():
            if node_val.get('type') not in meads.keys():
                continue
            mead_name = meads[node_val.get('type')]
            if not mead_dict.get(mead_name):
                mead_dict[mead_name] = {
                    'id': self._get_mead_id(mead_name, onboarded_meads),
                    'instances': [node_name]
                }
            else:
                mead_dict[mead_name]['instances'].append(node_name)
            if not node_val.get('requirements'):
                continue
            if not param_values.get(mead_name):
                param_values[mead_name] = {}
            param_values[mead_name]['substitution_mappings'] = dict()
            req_dict = dict()
            requirements = node_val.get('requirements')
            for requirement in requirements:
                req_name = list(requirement.keys())[0]
                req_val = list(requirement.values())[0]
                res_name = req_val + mes['mes']['mesd_id'][:11]
                req_dict[req_name] = res_name
                if req_val in mesd_dict['topology_template']['node_templates']:
                    param_values[mead_name]['substitution_mappings'][
                        res_name] = mesd_dict['topology_template'][
                            'node_templates'][req_val]

            param_values[mead_name]['substitution_mappings'][
                'requirements'] = req_dict
        mes['mead_details'] = mead_dict
        # Step-3
        kwargs = {'mes': mes, 'params': param_values}

        # NOTE NoTasksException is raised if no tasks.
        workflow = self._vim_drivers.invoke(
            driver_type,
            'prepare_and_create_workflow',
            resource='mea',
            action='create',
            auth_dict=self.get_auth_dict(context),
            kwargs=kwargs)
        try:
            mistral_execution = self._vim_drivers.invoke(
                driver_type,
                'execute_workflow',
                workflow=workflow,
                auth_dict=self.get_auth_dict(context))
        except Exception as ex:
            LOG.error('Error while executing workflow: %s', ex)
            self._vim_drivers.invoke(driver_type,
                                     'delete_workflow',
                                     workflow_id=workflow['id'],
                                     auth_dict=self.get_auth_dict(context))
            raise ex
        mes_dict = super(MeoPlugin, self).create_mes(context, mes)

        def _create_mes_wait(self_obj, mes_id, execution_id):
            exec_state = "RUNNING"
            mistral_retries = MISTRAL_RETRIES
            while exec_state == "RUNNING" and mistral_retries > 0:
                time.sleep(MISTRAL_RETRY_WAIT)
                exec_state = self._vim_drivers.invoke(
                    driver_type,
                    'get_execution',
                    execution_id=execution_id,
                    auth_dict=self.get_auth_dict(context)).state
                LOG.debug('status: %s', exec_state)
                if exec_state == 'SUCCESS' or exec_state == 'ERROR':
                    break
                mistral_retries = mistral_retries - 1
            error_reason = None
            if mistral_retries == 0 and exec_state == 'RUNNING':
                error_reason = _(
                    "MES creation is not completed within"
                    " {wait} seconds as creation of mistral"
                    " execution {mistral} is not completed").format(
                    wait=MISTRAL_RETRIES * MISTRAL_RETRY_WAIT,
                    mistral=execution_id)
            exec_obj = self._vim_drivers.invoke(
                driver_type,
                'get_execution',
                execution_id=execution_id,
                auth_dict=self.get_auth_dict(context))
            self._vim_drivers.invoke(driver_type,
                                     'delete_execution',
                                     execution_id=execution_id,
                                     auth_dict=self.get_auth_dict(context))
            self._vim_drivers.invoke(driver_type,
                                     'delete_workflow',
                                     workflow_id=workflow['id'],
                                     auth_dict=self.get_auth_dict(context))
            super(MeoPlugin, self).create_mes_post(context, mes_id, exec_obj,
                                                   mead_dict, error_reason)

        self.spawn_n(_create_mes_wait, self, mes_dict['id'],
                     mistral_execution.id)
        return mes_dict

    @log.log
    def _update_params(self, original, paramvalues):
        for key, value in (original).items():
            if not isinstance(value, dict) or 'get_input' not in str(value):
                pass
            elif isinstance(value, dict):
                if 'get_input' in value:
                    if value['get_input'] in paramvalues:
                        original[key] = paramvalues[value['get_input']]
                    else:
                        LOG.debug('Key missing Value: %s', key)
                        raise cs.InputValuesMissing(key=key)
                else:
                    self._update_params(value, paramvalues)

    @log.log
    def _process_parameterized_input(self, attrs, mesd_dict):
        param_vattrs_dict = attrs.pop('param_values', None)
        if param_vattrs_dict:
            for node in \
                    mesd_dict['topology_template']['node_templates'].values():
                if 'get_input' in str(node):
                    self._update_params(node, param_vattrs_dict['mesd'])
        else:
            raise cs.ParamYAMLInputMissing()

    @log.log
    def delete_mes(self, context, mes_id):
        mes = super(MeoPlugin, self).get_mes(context, mes_id)
        vim_res = self.vim_client.get_vim(context, mes['vim_id'])
        driver_type = vim_res['vim_type']
        workflow = None
        try:
            workflow = self._vim_drivers.invoke(
                driver_type,
                'prepare_and_create_workflow',
                resource='mea',
                action='delete',
                auth_dict=self.get_auth_dict(context),
                kwargs={
                    'mes': mes})
        except meo.NoTasksException:
            LOG.warning("No MEA deletion task(s).")
        if workflow:
            try:
                mistral_execution = self._vim_drivers.invoke(
                    driver_type,
                    'execute_workflow',
                    workflow=workflow,
                    auth_dict=self.get_auth_dict(context))

            except Exception as ex:
                LOG.error('Error while executing workflow: %s', ex)
                self._vim_drivers.invoke(driver_type,
                                         'delete_workflow',
                                         workflow_id=workflow['id'],
                                         auth_dict=self.get_auth_dict(context))

                raise ex
        super(MeoPlugin, self).delete_mes(context, mes_id)

        def _delete_mes_wait(mes_id, execution_id):
            exec_state = "RUNNING"
            mistral_retries = MISTRAL_RETRIES
            while exec_state == "RUNNING" and mistral_retries > 0:
                time.sleep(MISTRAL_RETRY_WAIT)
                exec_state = self._vim_drivers.invoke(
                    driver_type,
                    'get_execution',
                    execution_id=execution_id,
                    auth_dict=self.get_auth_dict(context)).state
                LOG.debug('status: %s', exec_state)
                if exec_state == 'SUCCESS' or exec_state == 'ERROR':
                    break
                mistral_retries -= 1
            error_reason = None
            if mistral_retries == 0 and exec_state == 'RUNNING':
                error_reason = _(
                    "MES deletion is not completed within"
                    " {wait} seconds as deletion of mistral"
                    " execution {mistral} is not completed").format(
                    wait=MISTRAL_RETRIES * MISTRAL_RETRY_WAIT,
                    mistral=execution_id)
            exec_obj = self._vim_drivers.invoke(
                driver_type,
                'get_execution',
                execution_id=execution_id,
                auth_dict=self.get_auth_dict(context))
            self._vim_drivers.invoke(driver_type,
                                     'delete_execution',
                                     execution_id=execution_id,
                                     auth_dict=self.get_auth_dict(context))
            self._vim_drivers.invoke(driver_type,
                                     'delete_workflow',
                                     workflow_id=workflow['id'],
                                     auth_dict=self.get_auth_dict(context))
            super(MeoPlugin, self).delete_mes_post(context, mes_id, exec_obj,
                                                   error_reason)
        if workflow:
            self.spawn_n(_delete_mes_wait, mes['id'], mistral_execution.id)
        else:
            super(MeoPlugin, self).delete_mes_post(
                context, mes_id, None, None)
        return mes['id']
