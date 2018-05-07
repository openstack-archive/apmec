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
from apmec.mem.infra_drivers.openstack import heat_client as hc
from apmec.mem.policy_actions import abstract_action
from apmec.mem import vim_client

LOG = logging.getLogger(__name__)


def _log_monitor_events(context, mea_dict, evt_details):
    _cos_db_plg = common_services_db_plugin.CommonServicesPluginDb()
    _cos_db_plg.create_event(context, res_id=mea_dict['id'],
                             res_type=constants.RES_TYPE_MEA,
                             res_state=mea_dict['status'],
                             evt_type=constants.RES_EVT_MONITOR,
                             tstamp=timeutils.utcnow(),
                             details=evt_details)


class MEAActionRespawn(abstract_action.AbstractPolicyAction):
    def get_type(self):
        return 'respawn'

    def get_name(self):
        return 'respawn'

    def get_description(self):
        return 'Apmec MEA respawning policy'

    def execute_action(self, plugin, context, mea_dict, args):
        mea_id = mea_dict['id']
        LOG.info('mea %s is dead and needs to be respawned', mea_id)
        attributes = mea_dict['attributes']
        vim_id = mea_dict['vim_id']

        def _update_failure_count():
            failure_count = int(attributes.get('failure_count', '0')) + 1
            failure_count_str = str(failure_count)
            LOG.debug("mea %(mea_id)s failure count %(failure_count)s",
                      {'mea_id': mea_id, 'failure_count': failure_count_str})
            attributes['failure_count'] = failure_count_str
            attributes['dead_instance_id_' + failure_count_str] = mea_dict[
                'instance_id']

        def _fetch_vim(vim_uuid):
            vim_res = vim_client.VimClient().get_vim(context, vim_uuid)
            return vim_res

        def _delete_heat_stack(vim_auth):
            placement_attr = mea_dict.get('placement_attr', {})
            region_name = placement_attr.get('region_name')
            heatclient = hc.HeatClient(auth_attr=vim_auth,
                                       region_name=region_name)
            heatclient.delete(mea_dict['instance_id'])
            LOG.debug("Heat stack %s delete initiated",
                      mea_dict['instance_id'])
            _log_monitor_events(context, mea_dict, "ActionRespawnHeat invoked")

        def _respawn_mea():
            update_mea_dict = plugin.create_mea_sync(context, mea_dict)
            LOG.info('respawned new mea %s', update_mea_dict['id'])
            plugin.config_mea(context, update_mea_dict)
            return update_mea_dict

        if plugin._mark_mea_dead(mea_dict['id']):
            _update_failure_count()
            vim_res = _fetch_vim(vim_id)
            if mea_dict['attributes'].get('monitoring_policy'):
                plugin._mea_monitor.mark_dead(mea_dict['id'])
                _delete_heat_stack(vim_res['vim_auth'])
                updated_mea = _respawn_mea()
                plugin.add_mea_to_monitor(context, updated_mea)
                LOG.debug("MEA %s added to monitor thread",
                          updated_mea['id'])
            if mea_dict['attributes'].get('alarming_policy'):
                _delete_heat_stack(vim_res['vim_auth'])
                mea_dict['attributes'].pop('alarming_policy')
                _respawn_mea()
