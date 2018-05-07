# Copyright 2013, 2014 Intel Corporation.
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

import inspect
import six
import yaml

import eventlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import uuidutils
from toscaparser.tosca_template import ToscaTemplate

from apmec.api.v1 import attributes
from apmec.common import driver_manager
from apmec.common import exceptions
from apmec.common import utils
from apmec.db.mem import mem_db
from apmec.extensions import mem
from apmec.plugins.common import constants
from apmec.mem.mgmt_drivers import constants as mgmt_constants
from apmec.mem import monitor
from apmec.mem import vim_client

from apmec.catalogs.tosca import utils as toscautils

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def config_opts():
    return [('apmec', MEMMgmtMixin.OPTS),
            ('apmec', MEMPlugin.OPTS_INFRA_DRIVER),
            ('apmec', MEMPlugin.OPTS_POLICY_ACTION)]


class MEMMgmtMixin(object):
    OPTS = [
        cfg.ListOpt(
            'mgmt_driver', default=['noop', 'openwrt'],
            help=_('MGMT driver to communicate with '
                   'Hosting MEA/logical service '
                   'instance apmec plugin will use')),
        cfg.IntOpt('boot_wait', default=30,
            help=_('Time interval to wait for VM to boot'))
    ]
    cfg.CONF.register_opts(OPTS, 'apmec')

    def __init__(self):
        super(MEMMgmtMixin, self).__init__()
        self._mgmt_manager = driver_manager.DriverManager(
            'apmec.apmec.mgmt.drivers', cfg.CONF.apmec.mgmt_driver)

    def _invoke(self, mea_dict, **kwargs):
        method = inspect.stack()[1][3]
        return self._mgmt_manager.invoke(
            self._mgmt_driver_name(mea_dict), method, **kwargs)

    def mgmt_create_pre(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_create_post(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_update_pre(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_update_post(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_delete_pre(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_delete_post(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_get_config(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_url(self, context, mea_dict):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict)

    def mgmt_call(self, context, mea_dict, kwargs):
        return self._invoke(
            mea_dict, plugin=self, context=context, mea=mea_dict,
            kwargs=kwargs)


class MEMPlugin(mem_db.MEMPluginDb, MEMMgmtMixin):
    """MEMPlugin which supports MEM framework.

    Plugin which supports Apmec framework
    """
    OPTS_INFRA_DRIVER = [
        cfg.ListOpt(
            'infra_driver', default=['noop', 'openstack'],
            help=_('Hosting mea drivers apmec plugin will use')),
    ]
    cfg.CONF.register_opts(OPTS_INFRA_DRIVER, 'apmec')

    OPTS_POLICY_ACTION = [
        cfg.ListOpt(
            'policy_action', default=['autoscaling', 'respawn',
                                      'log', 'log_and_kill'],
            help=_('Hosting mea drivers apmec plugin will use')),
    ]
    cfg.CONF.register_opts(OPTS_POLICY_ACTION, 'apmec')

    supported_extension_aliases = ['mem']

    def __init__(self):
        super(MEMPlugin, self).__init__()
        self._pool = eventlet.GreenPool()
        self.boot_wait = cfg.CONF.apmec.boot_wait
        self.vim_client = vim_client.VimClient()
        self._mea_manager = driver_manager.DriverManager(
            'apmec.apmec.mem.drivers',
            cfg.CONF.apmec.infra_driver)
        self._mea_action = driver_manager.DriverManager(
            'apmec.apmec.policy.actions',
            cfg.CONF.apmec.policy_action)
        self._mea_monitor = monitor.MEAMonitor(self.boot_wait)
        self._mea_alarm_monitor = monitor.MEAAlarmMonitor()

    def spawn_n(self, function, *args, **kwargs):
        self._pool.spawn_n(function, *args, **kwargs)

    def create_mead(self, context, mead):
        mead_data = mead['mead']
        template = mead_data['attributes'].get('mead')
        if isinstance(template, dict):
            # TODO(sripriya) remove this yaml dump once db supports storing
            # json format of yaml files in a separate column instead of
            # key value string pairs in mea attributes table
            mead_data['attributes']['mead'] = yaml.safe_dump(
                template)
        elif isinstance(template, str):
            self._report_deprecated_yaml_str()
        if "tosca_definitions_version" not in template:
            raise exceptions.Invalid('Not a valid template: '
                                     'tosca_definitions_version is missing.')

        LOG.debug('mead %s', mead_data)

        service_types = mead_data.get('service_types')
        if not attributes.is_attr_set(service_types):
            LOG.debug('service type must be specified')
            raise mem.ServiceTypesNotSpecified()
        for service_type in service_types:
            # TODO(yamahata):
            # framework doesn't know what services are valid for now.
            # so doesn't check it here yet.
            pass
        if 'template_source' in mead_data:
            template_source = mead_data.get('template_source')
        else:
            template_source = 'onboarded'
        mead['mead']['template_source'] = template_source

        self._parse_template_input(mead)
        return super(MEMPlugin, self).create_mead(
            context, mead)

    def _parse_template_input(self, mead):
        mead_dict = mead['mead']
        mead_yaml = mead_dict['attributes'].get('mead')
        if mead_yaml is None:
            return

        inner_mead_dict = yaml.safe_load(mead_yaml)
        LOG.debug('mead_dict: %s', inner_mead_dict)

        # Prepend the apmec_defs.yaml import file with the full
        # path to the file
        toscautils.updateimports(inner_mead_dict)

        try:
            tosca = ToscaTemplate(a_file=False,
                                  yaml_dict_tpl=inner_mead_dict)
        except Exception as e:
            LOG.exception("tosca-parser error: %s", str(e))
            raise mem.ToscaParserFailed(error_msg_details=str(e))

        if ('description' not in mead_dict or
                mead_dict['description'] == ''):
            mead_dict['description'] = inner_mead_dict.get(
                'description', '')
        if (('name' not in mead_dict or
                not len(mead_dict['name'])) and
                'metadata' in inner_mead_dict):
            mead_dict['name'] = inner_mead_dict['metadata'].get(
                'template_name', '')

        mead_dict['mgmt_driver'] = toscautils.get_mgmt_driver(
            tosca)
        LOG.debug('mead %s', mead)

    def add_mea_to_monitor(self, context, mea_dict):
        dev_attrs = mea_dict['attributes']
        mgmt_url = mea_dict['mgmt_url']
        if 'monitoring_policy' in dev_attrs and mgmt_url:
            def action_cb(action):
                LOG.debug('policy action: %s', action)
                self._mea_action.invoke(
                    action, 'execute_action', plugin=self, context=context,
                    mea_dict=hosting_mea['mea'], args={})

            hosting_mea = self._mea_monitor.to_hosting_mea(
                mea_dict, action_cb)
            LOG.debug('hosting_mea: %s', hosting_mea)
            self._mea_monitor.add_hosting_mea(hosting_mea)

    def add_alarm_url_to_mea(self, context, mea_dict):
        mead_yaml = mea_dict['mead']['attributes'].get('mead', '')
        mead_dict = yaml.safe_load(mead_yaml)
        if mead_dict and mead_dict.get('tosca_definitions_version'):
            polices = mead_dict['topology_template'].get('policies', [])
            for policy_dict in polices:
                name, policy = list(policy_dict.items())[0]
                if policy['type'] in constants.POLICY_ALARMING:
                    alarm_url =\
                        self._mea_alarm_monitor.update_mea_with_alarm(
                            self, context, mea_dict, policy)
                    mea_dict['attributes']['alarming_policy'] = mea_dict['id']
                    mea_dict['attributes'].update(alarm_url)
                    break

    def config_mea(self, context, mea_dict):
        config = mea_dict['attributes'].get('config')
        if not config:
            return
        eventlet.sleep(self.boot_wait)      # wait for vm to be ready
        mea_id = mea_dict['id']
        update = {
            'mea': {
                'id': mea_id,
                'attributes': {'config': config},
            }
        }
        self.update_mea(context, mea_id, update)

    def _get_infra_driver(self, context, mea_info):
        vim_res = self.get_vim(context, mea_info)
        return vim_res['vim_type'], vim_res['vim_auth']

    def _create_mea_wait(self, context, mea_dict, auth_attr, driver_name):
        mea_id = mea_dict['id']
        instance_id = self._instance_id(mea_dict)
        create_failed = False

        try:
            self._mea_manager.invoke(
                driver_name, 'create_wait', plugin=self, context=context,
                mea_dict=mea_dict, mea_id=instance_id,
                auth_attr=auth_attr)
        except mem.MEACreateWaitFailed as e:
            LOG.error("MEA Create failed for mea_id %s", mea_id)
            create_failed = True
            mea_dict['status'] = constants.ERROR
            self.set_mea_error_status_reason(context, mea_id,
                                             six.text_type(e))

        if instance_id is None or create_failed:
            mgmt_url = None
        else:
            # mgmt_url = self.mgmt_url(context, mea_dict)
            # FIXME(yamahata):
            mgmt_url = mea_dict['mgmt_url']

        self._create_mea_post(
            context, mea_id, instance_id, mgmt_url, mea_dict)
        self.mgmt_create_post(context, mea_dict)

        if instance_id is None or create_failed:
            return

        mea_dict['mgmt_url'] = mgmt_url

        kwargs = {
            mgmt_constants.KEY_ACTION: mgmt_constants.ACTION_CREATE_MEA,
            mgmt_constants.KEY_KWARGS: {'mea': mea_dict},
        }
        new_status = constants.ACTIVE
        try:
            self.mgmt_call(context, mea_dict, kwargs)
        except exceptions.MgmtDriverException:
            LOG.error('MEA configuration failed')
            new_status = constants.ERROR
            self.set_mea_error_status_reason(context, mea_id,
                                             'Unable to configure VDU')
        mea_dict['status'] = new_status
        self._create_mea_status(context, mea_id, new_status)

    def get_vim(self, context, mea):
        region_name = mea.setdefault('placement_attr', {}).get(
            'region_name', None)
        vim_res = self.vim_client.get_vim(context, mea['vim_id'],
                                          region_name)
        mea['placement_attr']['vim_name'] = vim_res['vim_name']
        mea['vim_id'] = vim_res['vim_id']
        return vim_res

    def _create_mea(self, context, mea, vim_auth, driver_name):
        mea_dict = self._create_mea_pre(
            context, mea) if not mea.get('id') else mea
        mea_id = mea_dict['id']
        LOG.debug('mea_dict %s', mea_dict)
        self.mgmt_create_pre(context, mea_dict)
        self.add_alarm_url_to_mea(context, mea_dict)
        try:
            instance_id = self._mea_manager.invoke(
                driver_name, 'create', plugin=self,
                context=context, mea=mea_dict, auth_attr=vim_auth)
        except Exception:
            LOG.debug('Fail to create mea %s in infra_driver, '
                      'so delete this mea',
                      mea_dict['id'])
            with excutils.save_and_reraise_exception():
                self.delete_mea(context, mea_id)

        if instance_id is None:
            self._create_mea_post(context, mea_id, None, None,
                                  mea_dict)
            return
        mea_dict['instance_id'] = instance_id
        return mea_dict

    def create_mea(self, context, mea):
        mea_info = mea['mea']
        name = mea_info['name']

        # if mead_template specified, create mead from template
        # create template dictionary structure same as needed in create_mead()
        if mea_info.get('mead_template'):
            mead_name = utils.generate_resource_name(name, 'inline')
            mead = {'mead': {'attributes': {'mead': mea_info['mead_template']},
                             'name': mead_name,
                             'template_source': 'inline',
                             'service_types': [{'service_type': 'mead'}]}}
            mea_info['mead_id'] = self.create_mead(context, mead).get('id')

        mea_attributes = mea_info['attributes']
        if mea_attributes.get('param_values'):
            param = mea_attributes['param_values']
            if isinstance(param, dict):
                # TODO(sripriya) remove this yaml dump once db supports storing
                # json format of yaml files in a separate column instead of
                #  key value string pairs in mea attributes table
                mea_attributes['param_values'] = yaml.safe_dump(param)
            else:
                self._report_deprecated_yaml_str()
        if mea_attributes.get('config'):
            config = mea_attributes['config']
            if isinstance(config, dict):
                # TODO(sripriya) remove this yaml dump once db supports storing
                # json format of yaml files in a separate column instead of
                #  key value string pairs in mea attributes table
                mea_attributes['config'] = yaml.safe_dump(config)
            else:
                self._report_deprecated_yaml_str()
        infra_driver, vim_auth = self._get_infra_driver(context, mea_info)
        if infra_driver not in self._mea_manager:
            LOG.debug('unknown vim driver '
                      '%(infra_driver)s in %(drivers)s',
                      {'infra_driver': infra_driver,
                       'drivers': cfg.CONF.apmec.infra_driver})
            raise mem.InvalidInfraDriver(vim_name=infra_driver)

        mea_dict = self._create_mea(context, mea_info, vim_auth, infra_driver)

        def create_mea_wait():
            self._create_mea_wait(context, mea_dict, vim_auth, infra_driver)
            if mea_dict['status'] is not constants.ERROR:
                self.add_mea_to_monitor(context, mea_dict)
            self.config_mea(context, mea_dict)
        self.spawn_n(create_mea_wait)
        return mea_dict

    # not for wsgi, but for service to create hosting mea
    # the mea is NOT added to monitor.
    def create_mea_sync(self, context, mea):
        infra_driver, vim_auth = self._get_infra_driver(context, mea)
        mea_dict = self._create_mea(context, mea, vim_auth, infra_driver)
        self._create_mea_wait(context, mea_dict, vim_auth, infra_driver)
        return mea_dict

    def _update_mea_wait(self, context, mea_dict, vim_auth, driver_name):
        instance_id = self._instance_id(mea_dict)
        kwargs = {
            mgmt_constants.KEY_ACTION: mgmt_constants.ACTION_UPDATE_MEA,
            mgmt_constants.KEY_KWARGS: {'mea': mea_dict},
        }
        new_status = constants.ACTIVE
        placement_attr = mea_dict['placement_attr']
        region_name = placement_attr.get('region_name')

        try:
            self._mea_manager.invoke(
                driver_name, 'update_wait', plugin=self,
                context=context, mea_id=instance_id, auth_attr=vim_auth,
                region_name=region_name)
            self.mgmt_call(context, mea_dict, kwargs)
        except exceptions.MgmtDriverException as e:
            LOG.error('MEA configuration failed')
            new_status = constants.ERROR
            self._mea_monitor.delete_hosting_mea(mea_dict['id'])
            self.set_mea_error_status_reason(context, mea_dict['id'],
                                             six.text_type(e))
        mea_dict['status'] = new_status
        self.mgmt_update_post(context, mea_dict)

        self._update_mea_post(context, mea_dict['id'],
                              new_status, mea_dict)

    def update_mea(self, context, mea_id, mea):
        mea_attributes = mea['mea']['attributes']
        if mea_attributes.get('config'):
            config = mea_attributes['config']
            if isinstance(config, dict):
                # TODO(sripriya) remove this yaml dump once db supports storing
                # json format of yaml files in a separate column instead of
                #  key value string pairs in mea attributes table
                mea_attributes['config'] = yaml.safe_dump(config)
            else:
                self._report_deprecated_yaml_str()
        mea_dict = self._update_mea_pre(context, mea_id)
        driver_name, vim_auth = self._get_infra_driver(context, mea_dict)
        instance_id = self._instance_id(mea_dict)

        try:
            self.mgmt_update_pre(context, mea_dict)
            self._mea_manager.invoke(
                driver_name, 'update', plugin=self, context=context,
                mea_id=instance_id, mea_dict=mea_dict,
                mea=mea, auth_attr=vim_auth)
        except Exception as e:
            with excutils.save_and_reraise_exception():
                mea_dict['status'] = constants.ERROR
                self._mea_monitor.delete_hosting_mea(mea_id)
                self.set_mea_error_status_reason(context,
                                                 mea_dict['id'],
                                                 six.text_type(e))
                self.mgmt_update_post(context, mea_dict)
                self._update_mea_post(context, mea_id,
                                      constants.ERROR,
                                      mea_dict)

        self.spawn_n(self._update_mea_wait, context, mea_dict, vim_auth,
                     driver_name)
        return mea_dict

    def _delete_mea_wait(self, context, mea_dict, auth_attr, driver_name):
        instance_id = self._instance_id(mea_dict)
        e = None
        if instance_id:
            placement_attr = mea_dict['placement_attr']
            region_name = placement_attr.get('region_name')
            try:
                self._mea_manager.invoke(
                    driver_name,
                    'delete_wait',
                    plugin=self,
                    context=context,
                    mea_id=instance_id,
                    auth_attr=auth_attr,
                    region_name=region_name)
            except Exception as e_:
                e = e_
                mea_dict['status'] = constants.ERROR
                mea_dict['error_reason'] = six.text_type(e)
                LOG.exception('_delete_mea_wait')
                self.set_mea_error_status_reason(context, mea_dict['id'],
                                                 mea_dict['error_reason'])

        self.mgmt_delete_post(context, mea_dict)
        self._delete_mea_post(context, mea_dict, e)

    def delete_mea(self, context, mea_id):
        mea_dict = self._delete_mea_pre(context, mea_id)
        driver_name, vim_auth = self._get_infra_driver(context, mea_dict)
        self._mea_monitor.delete_hosting_mea(mea_id)
        instance_id = self._instance_id(mea_dict)
        placement_attr = mea_dict['placement_attr']
        region_name = placement_attr.get('region_name')
        kwargs = {
            mgmt_constants.KEY_ACTION: mgmt_constants.ACTION_DELETE_MEA,
            mgmt_constants.KEY_KWARGS: {'mea': mea_dict},
        }
        try:
            self.mgmt_delete_pre(context, mea_dict)
            self.mgmt_call(context, mea_dict, kwargs)
            if instance_id:
                self._mea_manager.invoke(driver_name,
                                         'delete',
                                         plugin=self,
                                         context=context,
                                         mea_id=instance_id,
                                         auth_attr=vim_auth,
                                         region_name=region_name)
        except Exception as e:
            # TODO(yamahata): when the devaice is already deleted. mask
            # the error, and delete row in db
            # Other case mark error
            with excutils.save_and_reraise_exception():
                mea_dict['status'] = constants.ERROR
                mea_dict['error_reason'] = six.text_type(e)
                self.set_mea_error_status_reason(context, mea_dict['id'],
                                                 mea_dict['error_reason'])
                self.mgmt_delete_post(context, mea_dict)
                self._delete_mea_post(context, mea_dict, e)

        self.spawn_n(self._delete_mea_wait, context, mea_dict, vim_auth,
                     driver_name)

    def _handle_mea_scaling(self, context, policy):
        # validate
        def _validate_scaling_policy():
            type = policy['type']

            if type not in constants.POLICY_ACTIONS.keys():
                raise exceptions.MeaPolicyTypeInvalid(
                    type=type,
                    valid_types=constants.POLICY_ACTIONS.keys(),
                    policy=policy['name']
                )
            action = policy['action']

            if action not in constants.POLICY_ACTIONS[type]:
                raise exceptions.MeaPolicyActionInvalid(
                    action=action,
                    valid_actions=constants.POLICY_ACTIONS[type],
                    policy=policy['name']
                )

            LOG.debug("Policy %s is validated successfully", policy['name'])

        def _get_status():
            if policy['action'] == constants.ACTION_SCALE_IN:
                status = constants.PENDING_SCALE_IN
            else:
                status = constants.PENDING_SCALE_OUT

            return status

        # pre
        def _handle_mea_scaling_pre():
            status = _get_status()
            result = self._update_mea_scaling_status(context,
                                                     policy,
                                                     [constants.ACTIVE],
                                                     status)
            LOG.debug("Policy %(policy)s mea is at %(status)s",
                      {'policy': policy['name'],
                       'status': status})
            return result

        # post
        def _handle_mea_scaling_post(new_status, mgmt_url=None):
            status = _get_status()
            result = self._update_mea_scaling_status(context,
                                                     policy,
                                                     [status],
                                                     new_status,
                                                     mgmt_url)
            LOG.debug("Policy %(policy)s mea is at %(status)s",
                      {'policy': policy['name'],
                       'status': new_status})
            return result

        # action
        def _mea_policy_action():
            try:
                last_event_id = self._mea_manager.invoke(
                    infra_driver,
                    'scale',
                    plugin=self,
                    context=context,
                    auth_attr=vim_auth,
                    policy=policy,
                    region_name=region_name
                )
                LOG.debug("Policy %s action is started successfully",
                          policy['name'])
                return last_event_id
            except Exception as e:
                LOG.error("Policy %s action is failed to start",
                          policy)
                with excutils.save_and_reraise_exception():
                    mea['status'] = constants.ERROR
                    self.set_mea_error_status_reason(
                        context,
                        policy['mea']['id'],
                        six.text_type(e))
                    _handle_mea_scaling_post(constants.ERROR)

        # wait
        def _mea_policy_action_wait():
            try:
                LOG.debug("Policy %s action is in progress",
                          policy['name'])
                mgmt_url = self._mea_manager.invoke(
                    infra_driver,
                    'scale_wait',
                    plugin=self,
                    context=context,
                    auth_attr=vim_auth,
                    policy=policy,
                    region_name=region_name,
                    last_event_id=last_event_id
                )
                LOG.debug("Policy %s action is completed successfully",
                          policy['name'])
                _handle_mea_scaling_post(constants.ACTIVE, mgmt_url)
                # TODO(kanagaraj-manickam): Add support for config and mgmt
            except Exception as e:
                LOG.error("Policy %s action is failed to complete",
                          policy['name'])
                with excutils.save_and_reraise_exception():
                    self.set_mea_error_status_reason(
                        context,
                        policy['mea']['id'],
                        six.text_type(e))
                    _handle_mea_scaling_post(constants.ERROR)

        _validate_scaling_policy()

        mea = _handle_mea_scaling_pre()
        policy['instance_id'] = mea['instance_id']

        infra_driver, vim_auth = self._get_infra_driver(context, mea)
        region_name = mea.get('placement_attr', {}).get('region_name', None)
        last_event_id = _mea_policy_action()
        self.spawn_n(_mea_policy_action_wait)

        return policy

    def _report_deprecated_yaml_str(self):
        utils.deprecate_warning(what='yaml as string',
                                as_of='N', in_favor_of='yaml as dictionary')

    def _make_policy_dict(self, mea, name, policy):
        p = {}
        p['type'] = policy.get('type')
        p['properties'] = policy.get('properties') or policy.get('triggers')
        p['mea'] = mea
        p['name'] = name
        p['id'] = uuidutils.generate_uuid()
        return p

    def get_mea_policies(
            self, context, mea_id, filters=None, fields=None):
        mea = self.get_mea(context, mea_id)
        mead_tmpl = yaml.safe_load(mea['mead']['attributes']['mead'])
        policy_list = []

        polices = mead_tmpl['topology_template'].get('policies', [])
        for policy_dict in polices:
            for name, policy in policy_dict.items():
                def _add(policy):
                    p = self._make_policy_dict(mea, name, policy)
                    p['name'] = name
                    policy_list.append(p)

                # Check for filters
                if filters.get('name') or filters.get('type'):
                    if name == filters.get('name'):
                        _add(policy)
                        break
                    elif policy['type'] == filters.get('type'):
                        _add(policy)
                        break
                    else:
                        continue

                _add(policy)

        return policy_list

    def get_mea_policy(
            self, context, policy_id, mea_id, fields=None):
        policies = self.get_mea_policies(context,
                                         mea_id,
                                         filters={'name': policy_id})
        if policies:
            return policies[0]
        else:
            return None

    def create_mea_scale(self, context, mea_id, scale):
        policy_ = self.get_mea_policy(context,
                                      scale['scale']['policy'],
                                      mea_id)
        if not policy_:
            raise exceptions.MeaPolicyNotFound(policy=scale['scale']['policy'],
                                               mea_id=mea_id)
        policy_.update({'action': scale['scale']['type']})
        self._handle_mea_scaling(context, policy_)

        return scale['scale']

    def get_mea_policy_by_type(self, context, mea_id, policy_type=None, fields=None):             # noqa
        policies = self.get_mea_policies(context,
                                         mea_id,
                                         filters={'type': policy_type})
        if policies:
            return policies[0]

        raise exceptions.MeaPolicyTypeInvalid(type=constants.POLICY_ALARMING,
                                              mea_id=mea_id)

    def _validate_alarming_policy(self, context, mea_id, trigger):
        # validate alarm status
        if not self._mea_alarm_monitor.process_alarm_for_mea(mea_id, trigger):
            raise exceptions.AlarmUrlInvalid(mea_id=mea_id)

        # validate policy action. if action is composite, split it.
        # ex: respawn%notify
        action = trigger['action_name']
        action_list = action.split('%')
        pl_action_dict = dict()
        pl_action_dict['policy_actions'] = dict()
        pl_action_dict['policy_actions']['def_actions'] = list()
        pl_action_dict['policy_actions']['custom_actions'] = dict()
        for action in action_list:
            # validate policy action. if action is composite, split it.
            # ex: SP1-in, SP1-out
            action_ = None
            if action in constants.DEFAULT_ALARM_ACTIONS:
                pl_action_dict['policy_actions']['def_actions'].append(action)
            policy_ = self.get_mea_policy(context, action, mea_id)
            if not policy_:
                sp_action = action.split('-')
                if len(sp_action) == 2:
                    bk_policy_name = sp_action[0]
                    bk_policy_action = sp_action[1]
                    policies_ = self.get_mea_policies(
                        context, mea_id, filters={'name': bk_policy_name})
                    if policies_:
                        policy_ = policies_[0]
                        action_ = bk_policy_action
            if policy_:
                pl_action_dict['policy_actions']['custom_actions'].update(
                    {policy_['id']: {'bckend_policy': policy_,
                                   'bckend_action': action_}})

            LOG.debug("Trigger %s is validated successfully", trigger)

        return pl_action_dict
        # validate url

    def _get_mea_triggers(self, context, mea_id, filters=None, fields=None):
        policy = self.get_mea_policy_by_type(
            context, mea_id, policy_type=constants.POLICY_ALARMING)
        triggers = policy['properties']
        mea_trigger = dict()
        for trigger_name, trigger_dict in triggers.items():
            if trigger_name == filters.get('name'):
                mea_trigger['trigger'] = {trigger_name: trigger_dict}
                mea_trigger['mea'] = policy['mea']
                break

        return mea_trigger

    def get_mea_trigger(self, context, mea_id, trigger_name):
        trigger = self._get_mea_triggers(
            context, mea_id, filters={'name': trigger_name})
        if not trigger:
            raise exceptions.TriggerNotFound(
                trigger_name=trigger_name,
                mea_id=mea_id
            )
        return trigger

    def _handle_mea_monitoring(self, context, trigger):
        mea_dict = trigger['mea']
        if trigger['action_name'] in constants.DEFAULT_ALARM_ACTIONS:
            action = trigger['action_name']
            LOG.debug('mea for monitoring: %s', mea_dict)
            self._mea_action.invoke(
                action, 'execute_action', plugin=self, context=context,
                mea_dict=mea_dict, args={})

        # Multiple actions support
        if trigger.get('policy_actions'):
            policy_actions = trigger['policy_actions']
            if policy_actions.get('def_actions'):
                for action in policy_actions['def_actions']:
                    self._mea_action.invoke(
                        action, 'execute_action', plugin=self, context=context,
                        mea_dict=mea_dict, args={})
            if policy_actions.get('custom_actions'):
                custom_actions = policy_actions['custom_actions']
                for pl_action, pl_action_dict in custom_actions.items():
                    bckend_policy = pl_action_dict['bckend_policy']
                    bckend_action = pl_action_dict['bckend_action']
                    bckend_policy_type = bckend_policy['type']
                    if bckend_policy_type == constants.POLICY_SCALING:
                        if mea_dict['status'] != constants.ACTIVE:
                            LOG.info(_("Scaling Policy action"
                                       "skipped due to status:"
                                       "%(status)s for mea: %(meaid)s"),
                                     {"status": mea_dict['status'],
                                      "meaid": mea_dict['id']})
                            return
                        action = 'autoscaling'
                        scale = {}
                        scale.setdefault('scale', {})
                        scale['scale']['type'] = bckend_action
                        scale['scale']['policy'] = bckend_policy['name']
                        self._mea_action.invoke(
                            action, 'execute_action', plugin=self,
                            context=context, mea_dict=mea_dict, args=scale)

    def create_mea_trigger(
            self, context, mea_id, trigger):
        trigger_ = self.get_mea_trigger(
            context, mea_id, trigger['trigger']['policy_name'])
        # action_name before analyzing
        trigger_.update({'action_name': trigger['trigger']['action_name']})
        trigger_.update({'params': trigger['trigger']['params']})
        policy_actions = self._validate_alarming_policy(
            context, mea_id, trigger_)
        if policy_actions:
            trigger_.update(policy_actions)
        self._handle_mea_monitoring(context, trigger_)
        return trigger['trigger']

    def get_mea_resources(self, context, mea_id, fields=None, filters=None):
        mea_info = self.get_mea(context, mea_id)
        infra_driver, vim_auth = self._get_infra_driver(context, mea_info)
        if mea_info['status'] == constants.ACTIVE:
            mea_details = self._mea_manager.invoke(infra_driver,
                                                   'get_resource_info',
                                                   plugin=self,
                                                   context=context,
                                                   mea_info=mea_info,
                                                   auth_attr=vim_auth)
            resources = [{'name': name,
                          'type': info.get('type'),
                          'id': info.get('id')}
                        for name, info in mea_details.items()]
            return resources
        # Raise exception when MEA.status != ACTIVE
        else:
            raise mem.MEAInactive(mea_id=mea_id,
                                   message=_(' Cannot fetch details'))
