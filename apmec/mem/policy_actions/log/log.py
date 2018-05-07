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
#

from oslo_log import log as logging
from oslo_utils import timeutils

from apmec.db.common_services import common_services_db_plugin
from apmec.plugins.common import constants
from apmec.mem.policy_actions import abstract_action

LOG = logging.getLogger(__name__)


def _log_monitor_events(context, mea_dict, evt_details):
    _cos_db_plg = common_services_db_plugin.CommonServicesPluginDb()
    _cos_db_plg.create_event(context, res_id=mea_dict['id'],
                             res_type=constants.RES_TYPE_MEA,
                             res_state=mea_dict['status'],
                             evt_type=constants.RES_EVT_MONITOR,
                             tstamp=timeutils.utcnow(),
                             details=evt_details)


class MEAActionLog(abstract_action.AbstractPolicyAction):
    def get_type(self):
        return 'log'

    def get_name(self):
        return 'log'

    def get_description(self):
        return 'Apmec MEA logging policy'

    def execute_action(self, plugin, context, mea_dict, args):
        mea_id = mea_dict['id']
        LOG.error('mea %s dead', mea_id)
        _log_monitor_events(context,
                            mea_dict,
                            "ActionLogOnly invoked")


class MEAActionLogAndKill(abstract_action.AbstractPolicyAction):
    def get_type(self):
        return 'log_and_kill'

    def get_name(self):
        return 'log_and_kill'

    def get_description(self):
        return 'Apmec MEA log_and_kill policy'

    def execute_action(self, plugin, context, mea_dict, args):
        _log_monitor_events(context,
                            mea_dict,
                            "ActionLogAndKill invoked")
        mea_id = mea_dict['id']
        if plugin._mark_mea_dead(mea_dict['id']):
            if mea_dict['attributes'].get('monitoring_policy'):
                plugin._mea_monitor.mark_dead(mea_dict['id'])
            plugin.delete_mea(context, mea_id)
        LOG.error('mea %s dead', mea_id)
