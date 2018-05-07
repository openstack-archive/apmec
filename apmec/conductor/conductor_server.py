# Copyright 2017 OpenStack Foundation
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

import sys

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging
from oslo_service import service
from oslo_utils import timeutils
from sqlalchemy.orm import exc as orm_exc

from apmec.common import topics
from apmec import context as t_context
from apmec.db.common_services import common_services_db
from apmec.db.meo import meo_db
from apmec.extensions import meo
from apmec import manager
from apmec.plugins.common import constants
from apmec import service as apmec_service
from apmec import version


LOG = logging.getLogger(__name__)


class Conductor(manager.Manager):
    def __init__(self, host, conf=None):
        if conf:
            self.conf = conf
        else:
            self.conf = cfg.CONF
        super(Conductor, self).__init__(host=self.conf.host)

    def update_vim(self, context, vim_id, status):
        t_admin_context = t_context.get_admin_context()
        update_time = timeutils.utcnow()
        with t_admin_context.session.begin(subtransactions=True):
            try:
                query = t_admin_context.session.query(meo_db.Vim)
                query.filter(
                    meo_db.Vim.id == vim_id).update(
                        {'status': status,
                         'updated_at': update_time})
            except orm_exc.NoResultFound:
                raise meo.VimNotFoundException(vim_id=vim_id)
            event_db = common_services_db.Event(
                resource_id=vim_id,
                resource_type=constants.RES_TYPE_VIM,
                resource_state=status,
                event_details="",
                event_type=constants.RES_EVT_MONITOR,
                timestamp=update_time)
            t_admin_context.session.add(event_db)
        return status


def init(args, **kwargs):
    cfg.CONF(args=args, project='apmec',
             version='%%prog %s' % version.version_info.release_string(),
             **kwargs)

    # FIXME(ihrachys): if import is put in global, circular import
    # failure occurs
    from apmec.common import rpc as n_rpc
    n_rpc.init(cfg.CONF)


def main(manager='apmec.conductor.conductor_server.Conductor'):
    init(sys.argv[1:])
    logging.setup(cfg.CONF, "apmec")
    oslo_messaging.set_transport_defaults(control_exchange='apmec')
    logging.setup(cfg.CONF, "apmec")
    cfg.CONF.log_opt_values(LOG, logging.DEBUG)
    server = apmec_service.Service.create(
        binary='apmec-conductor',
        topic=topics.TOPIC_CONDUCTOR,
        manager=manager)
    service.launch(cfg.CONF, server).wait()
