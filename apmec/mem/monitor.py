# Copyright 2015 Intel Corporation.
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
import threading
import time

from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils
from oslo_utils import timeutils


from apmec.common import driver_manager
from apmec import context as t_context
from apmec.db.common_services import common_services_db_plugin
from apmec.plugins.common import constants

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
OPTS = [
    cfg.IntOpt('check_intvl',
               default=10,
               help=_("check interval for monitor")),
]
CONF.register_opts(OPTS, group='monitor')


def config_opts():
    return [('monitor', OPTS),
            ('apmec', MEAMonitor.OPTS),
            ('apmec', MEAAlarmMonitor.OPTS), ]


def _log_monitor_events(context, mea_dict, evt_details):
    _cos_db_plg = common_services_db_plugin.CommonServicesPluginDb()
    _cos_db_plg.create_event(context, res_id=mea_dict['id'],
                             res_type=constants.RES_TYPE_MEA,
                             res_state=mea_dict['status'],
                             evt_type=constants.RES_EVT_MONITOR,
                             tstamp=timeutils.utcnow(),
                             details=evt_details)


class MEAMonitor(object):
    """MEA Monitor."""

    _instance = None
    _hosting_meas = dict()   # mea_id => dict of parameters
    _status_check_intvl = 0
    _lock = threading.RLock()

    OPTS = [
        cfg.ListOpt(
            'monitor_driver', default=['ping', 'http_ping'],
            help=_('Monitor driver to communicate with '
                   'Hosting MEA/logical service '
                   'instance apmec plugin will use')),
    ]
    cfg.CONF.register_opts(OPTS, 'apmec')

    def __new__(cls, boot_wait, check_intvl=None):
        if not cls._instance:
            cls._instance = super(MEAMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self, boot_wait, check_intvl=None):
        self._monitor_manager = driver_manager.DriverManager(
            'apmec.apmec.monitor.drivers',
            cfg.CONF.apmec.monitor_driver)

        self.boot_wait = boot_wait
        if check_intvl is None:
            check_intvl = cfg.CONF.monitor.check_intvl
        self._status_check_intvl = check_intvl
        LOG.debug('Spawning MEA monitor thread')
        threading.Thread(target=self.__run__).start()

    def __run__(self):
        while(1):
            time.sleep(self._status_check_intvl)

            with self._lock:
                for hosting_mea in self._hosting_meas.values():
                    if hosting_mea.get('dead', False):
                        LOG.debug('monitor skips dead mea %s', hosting_mea)
                        continue

                    self.run_monitor(hosting_mea)

    @staticmethod
    def to_hosting_mea(mea_dict, action_cb):
        return {
            'id': mea_dict['id'],
            'management_ip_addresses': jsonutils.loads(
                mea_dict['mgmt_url']),
            'action_cb': action_cb,
            'mea': mea_dict,
            'monitoring_policy': jsonutils.loads(
                mea_dict['attributes']['monitoring_policy'])
        }

    def add_hosting_mea(self, new_mea):
        LOG.debug('Adding host %(id)s, Mgmt IP %(ips)s',
                  {'id': new_mea['id'],
                   'ips': new_mea['management_ip_addresses']})
        new_mea['boot_at'] = timeutils.utcnow()
        with self._lock:
            self._hosting_meas[new_mea['id']] = new_mea

        attrib_dict = new_mea['mea']['attributes']
        mon_policy_dict = attrib_dict['monitoring_policy']
        evt_details = (("MEA added for monitoring. "
                        "mon_policy_dict = %s,") % (mon_policy_dict))
        _log_monitor_events(t_context.get_admin_context(), new_mea['mea'],
                            evt_details)

    def delete_hosting_mea(self, mea_id):
        LOG.debug('deleting mea_id %(mea_id)s', {'mea_id': mea_id})
        with self._lock:
            hosting_mea = self._hosting_meas.pop(mea_id, None)
            if hosting_mea:
                LOG.debug('deleting mea_id %(mea_id)s, Mgmt IP %(ips)s',
                          {'mea_id': mea_id,
                           'ips': hosting_mea['management_ip_addresses']})

    def run_monitor(self, hosting_mea):
        mgmt_ips = hosting_mea['management_ip_addresses']
        vdupolicies = hosting_mea['monitoring_policy']['vdus']

        mea_delay = hosting_mea['monitoring_policy'].get(
            'monitoring_delay', self.boot_wait)

        for vdu in vdupolicies.keys():
            if hosting_mea.get('dead'):
                return

            policy = vdupolicies[vdu]
            for driver in policy.keys():
                params = policy[driver].get('monitoring_params', {})

                vdu_delay = params.get('monitoring_delay', mea_delay)

                if not timeutils.is_older_than(
                    hosting_mea['boot_at'],
                        vdu_delay):
                        continue

                actions = policy[driver].get('actions', {})
                if 'mgmt_ip' not in params:
                    params['mgmt_ip'] = mgmt_ips[vdu]

                driver_return = self.monitor_call(driver,
                                                  hosting_mea['mea'],
                                                  params)

                LOG.debug('driver_return %s', driver_return)

                if driver_return in actions:
                    action = actions[driver_return]
                    hosting_mea['action_cb'](action)

    def mark_dead(self, mea_id):
        self._hosting_meas[mea_id]['dead'] = True

    def _invoke(self, driver, **kwargs):
        method = inspect.stack()[1][3]
        return self._monitor_manager.invoke(
            driver, method, **kwargs)

    def monitor_get_config(self, mea_dict):
        return self._invoke(
            mea_dict, monitor=self, mea=mea_dict)

    def monitor_url(self, mea_dict):
        return self._invoke(
            mea_dict, monitor=self, mea=mea_dict)

    def monitor_call(self, driver, mea_dict, kwargs):
        return self._invoke(driver,
                            mea=mea_dict, kwargs=kwargs)


class MEAAlarmMonitor(object):
    """MEA Alarm monitor"""
    OPTS = [
        cfg.ListOpt(
            'alarm_monitor_driver', default=['ceilometer'],
            help=_('Alarm monitoring driver to communicate with '
                   'Hosting MEA/logical service '
                   'instance apmec plugin will use')),
    ]
    cfg.CONF.register_opts(OPTS, 'apmec')

    # get alarm here
    def __init__(self):
        self._alarm_monitor_manager = driver_manager.DriverManager(
            'apmec.apmec.alarm_monitor.drivers',
            cfg.CONF.apmec.alarm_monitor_driver)

    def update_mea_with_alarm(self, plugin, context, mea, policy_dict):
        triggers = policy_dict['triggers']
        alarm_url = dict()
        for trigger_name, trigger_dict in triggers.items():
            params = dict()
            params['mea_id'] = mea['id']
            params['mon_policy_name'] = trigger_name
            driver = trigger_dict['event_type']['implementation']
            # TODO(Tung Doan) trigger_dict.get('actions') needs to be used
            policy_action = trigger_dict.get('action')
            if len(policy_action) == 0:
                _log_monitor_events(t_context.get_admin_context(),
                                    mea,
                                    "Alarm not set: policy action missing")
                return
            # Other backend policies with the construct (policy, action)
            # ex: (SP1, in), (SP1, out)

            def _refactor_backend_policy(bk_policy_name, bk_action_name):
                policy = '%(policy_name)s-%(action_name)s' % {
                    'policy_name': bk_policy_name,
                    'action_name': bk_action_name}
                return policy

            for index, policy_action_name in enumerate(policy_action):
                filters = {'name': policy_action_name}
                bkend_policies =\
                    plugin.get_mea_policies(context, mea['id'], filters)
                if bkend_policies:
                    bkend_policy = bkend_policies[0]
                    if bkend_policy['type'] == constants.POLICY_SCALING:
                        cp = trigger_dict['condition'].\
                            get('comparison_operator')
                        scaling_type = 'out' if cp == 'gt' else 'in'
                        policy_action[index] = _refactor_backend_policy(
                            policy_action_name, scaling_type)

            # Support multiple action. Ex: respawn % notify
            action_name = '%'.join(policy_action)

            params['mon_policy_action'] = action_name
            alarm_url[trigger_name] =\
                self.call_alarm_url(driver, mea, params)
            details = "Alarm URL set successfully: %s" % alarm_url
            _log_monitor_events(t_context.get_admin_context(),
                                mea,
                                details)
        return alarm_url

    def process_alarm_for_mea(self, mea, trigger):
        '''call in plugin'''
        params = trigger['params']
        mon_prop = trigger['trigger']
        alarm_dict = dict()
        alarm_dict['alarm_id'] = params['data'].get('alarm_id')
        alarm_dict['status'] = params['data'].get('current')
        trigger_name, trigger_dict = list(mon_prop.items())[0]
        driver = trigger_dict['event_type']['implementation']
        return self.process_alarm(driver, mea, alarm_dict)

    def _invoke(self, driver, **kwargs):
        method = inspect.stack()[1][3]
        return self._alarm_monitor_manager.invoke(
            driver, method, **kwargs)

    def call_alarm_url(self, driver, mea_dict, kwargs):
        return self._invoke(driver,
                            mea=mea_dict, kwargs=kwargs)

    def process_alarm(self, driver, mea_dict, kwargs):
        return self._invoke(driver,
                            mea=mea_dict, kwargs=kwargs)
