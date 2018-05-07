# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ast
from datetime import datetime

from oslo_db.exception import DBDuplicateEntry
from oslo_log import log as logging
from oslo_utils import timeutils
from oslo_utils import uuidutils
from six import iteritems

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy import schema

from apmec.common import exceptions
from apmec.db.common_services import common_services_db_plugin
from apmec.db import db_base
from apmec.db import model_base
from apmec.db import models_v1
from apmec.db import types
from apmec.extensions import meo
from apmec.extensions.meo_plugins import edge_service
from apmec.plugins.common import constants

LOG = logging.getLogger(__name__)
_ACTIVE_UPDATE = (constants.ACTIVE, constants.PENDING_UPDATE)
_ACTIVE_UPDATE_ERROR_DEAD = (
    constants.PENDING_CREATE, constants.ACTIVE, constants.PENDING_UPDATE,
    constants.ERROR, constants.DEAD)
CREATE_STATES = (constants.PENDING_CREATE, constants.DEAD)


###########################################################################
# db tables

class MESD(model_base.BASE, models_v1.HasId, models_v1.HasTenant,
        models_v1.Audit):
    """Represents MESD to create MES."""

    __tablename__ = 'mesd'
    # Descriptive name
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    meads = sa.Column(types.Json, nullable=True)

    # Mesd template source - onboarded
    template_source = sa.Column(sa.String(255), server_default='onboarded')

    # (key, value) pair to spin up
    attributes = orm.relationship('MESDAttribute',
                                  backref='mesd')

    __table_args__ = (
        schema.UniqueConstraint(
            "tenant_id",
            "name",
            name="uniq_mesd0tenant_id0name"),
    )


class MESDAttribute(model_base.BASE, models_v1.HasId):
    """Represents attributes necessary for creation of mes in (key, value) pair

    """

    __tablename__ = 'mesd_attribute'
    mesd_id = sa.Column(types.Uuid, sa.ForeignKey('mesd.id'),
            nullable=False)
    key = sa.Column(sa.String(255), nullable=False)
    value = sa.Column(sa.TEXT(65535), nullable=True)


class MES(model_base.BASE, models_v1.HasId, models_v1.HasTenant,
        models_v1.Audit):
    """Represents network services that deploys services.

    """

    __tablename__ = 'mes'
    mesd_id = sa.Column(types.Uuid, sa.ForeignKey('mesd.id'))
    mesd = orm.relationship('MESD')

    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text, nullable=True)

    # Dict of MEA details that network service launches
    mea_ids = sa.Column(sa.TEXT(65535), nullable=True)

    # Dict of mgmt urls that network servic launches
    mgmt_urls = sa.Column(sa.TEXT(65535), nullable=True)

    status = sa.Column(sa.String(64), nullable=False)
    vim_id = sa.Column(types.Uuid, sa.ForeignKey('vims.id'), nullable=False)
    error_reason = sa.Column(sa.Text, nullable=True)

    __table_args__ = (
        schema.UniqueConstraint(
            "tenant_id",
            "name",
            name="uniq_mes0tenant_id0name"),
    )


class MESPluginDb(edge_service.MESPluginBase, db_base.CommonDbMixin):

    def __init__(self):
        super(MESPluginDb, self).__init__()
        self._cos_db_plg = common_services_db_plugin.CommonServicesPluginDb()

    def _get_resource(self, context, model, id):
        try:
            return self._get_by_id(context, model, id)
        except orm_exc.NoResultFound:
            if issubclass(model, MESD):
                raise edge_service.MESDNotFound(mesd_id=id)
            if issubclass(model, MES):
                raise edge_service.MESNotFound(mes_id=id)
            else:
                raise

    def _get_mes_db(self, context, mes_id, current_statuses, new_status):
        try:
            mes_db = (
                self._model_query(context, MES).
                filter(MES.id == mes_id).
                filter(MES.status.in_(current_statuses)).
                with_lockmode('update').one())
        except orm_exc.NoResultFound:
            raise edge_service.MESNotFound(mes_id=mes_id)
        mes_db.update({'status': new_status})
        return mes_db

    def _make_attributes_dict(self, attributes_db):
        return dict((attr.key, attr.value) for attr in attributes_db)

    def _make_mesd_dict(self, mesd, fields=None):
        res = {
            'attributes': self._make_attributes_dict(mesd['attributes']),
        }
        key_list = ('id', 'tenant_id', 'name', 'description',
                    'created_at', 'updated_at', 'meads', 'template_source')
        res.update((key, mesd[key]) for key in key_list)
        return self._fields(res, fields)

    def _make_dev_attrs_dict(self, dev_attrs_db):
        return dict((arg.key, arg.value) for arg in dev_attrs_db)

    def _make_mes_dict(self, mes_db, fields=None):
        LOG.debug('mes_db %s', mes_db)
        res = {}
        key_list = ('id', 'tenant_id', 'mesd_id', 'name', 'description',
                    'mea_ids', 'status', 'mgmt_urls', 'error_reason',
                    'vim_id', 'created_at', 'updated_at')
        res.update((key, mes_db[key]) for key in key_list)
        return self._fields(res, fields)

    def create_mesd(self, context, mesd):
        meads = mesd['meads']
        mesd = mesd['mesd']
        LOG.debug('mesd %s', mesd)
        tenant_id = self._get_tenant_id_for_create(context, mesd)
        template_source = mesd.get('template_source')

        try:
            with context.session.begin(subtransactions=True):
                mesd_id = uuidutils.generate_uuid()
                mesd_db = MESD(
                    id=mesd_id,
                    tenant_id=tenant_id,
                    name=mesd.get('name'),
                    meads=meads,
                    description=mesd.get('description'),
                    deleted_at=datetime.min,
                    template_source=template_source)
                context.session.add(mesd_db)
                for (key, value) in mesd.get('attributes', {}).items():
                    attribute_db = MESDAttribute(
                        id=uuidutils.generate_uuid(),
                        mesd_id=mesd_id,
                        key=key,
                        value=value)
                    context.session.add(attribute_db)
        except DBDuplicateEntry as e:
            raise exceptions.DuplicateEntity(
                _type="mesd",
                entry=e.columns)
        LOG.debug('mesd_db %(mesd_db)s %(attributes)s ',
                  {'mesd_db': mesd_db,
                   'attributes': mesd_db.attributes})
        mesd_dict = self._make_mesd_dict(mesd_db)
        LOG.debug('mesd_dict %s', mesd_dict)
        self._cos_db_plg.create_event(
            context, res_id=mesd_dict['id'],
            res_type=constants.RES_TYPE_MESD,
            res_state=constants.RES_EVT_ONBOARDED,
            evt_type=constants.RES_EVT_CREATE,
            tstamp=mesd_dict[constants.RES_EVT_CREATED_FLD])
        return mesd_dict

    def delete_mesd(self,
            context,
            mesd_id,
            soft_delete=True):
        with context.session.begin(subtransactions=True):
            mess_db = context.session.query(MES).filter_by(
                mesd_id=mesd_id).first()
            if mess_db is not None and mess_db.deleted_at is None:
                raise meo.MESDInUse(mesd_id=mesd_id)

            mesd_db = self._get_resource(context, MESD,
                                        mesd_id)
            if soft_delete:
                mesd_db.update({'deleted_at': timeutils.utcnow()})
                self._cos_db_plg.create_event(
                    context, res_id=mesd_db['id'],
                    res_type=constants.RES_TYPE_MESD,
                    res_state=constants.RES_EVT_NA_STATE,
                    evt_type=constants.RES_EVT_DELETE,
                    tstamp=mesd_db[constants.RES_EVT_DELETED_FLD])
            else:
                context.session.query(MESDAttribute).filter_by(
                    mesd_id=mesd_id).delete()
                context.session.delete(mesd_db)

    def get_mesd(self, context, mesd_id, fields=None):
        mesd_db = self._get_resource(context, MESD, mesd_id)
        return self._make_mesd_dict(mesd_db)

    def get_mesds(self, context, filters, fields=None):
        if ('template_source' in filters) and \
                (filters['template_source'][0] == 'all'):
            filters.pop('template_source')
        return self._get_collection(context, MESD,
                                    self._make_mesd_dict,
                                    filters=filters, fields=fields)

    # reference implementation. needs to be overrided by subclass
    def create_mes(self, context, mes):
        LOG.debug('mes %s', mes)
        mes = mes['mes']
        tenant_id = self._get_tenant_id_for_create(context, mes)
        mesd_id = mes['mesd_id']
        vim_id = mes['vim_id']
        name = mes.get('name')
        mes_id = uuidutils.generate_uuid()
        try:
            with context.session.begin(subtransactions=True):
                mesd_db = self._get_resource(context, MESD,
                                            mesd_id)
                mes_db = MES(id=mes_id,
                           tenant_id=tenant_id,
                           name=name,
                           description=mesd_db.description,
                           mea_ids=None,
                           status=constants.PENDING_CREATE,
                           mgmt_urls=None,
                           mesd_id=mesd_id,
                           vim_id=vim_id,
                           error_reason=None,
                           deleted_at=datetime.min)
                context.session.add(mes_db)
        except DBDuplicateEntry as e:
            raise exceptions.DuplicateEntity(
                _type="mes",
                entry=e.columns)
        evt_details = "MES UUID assigned."
        self._cos_db_plg.create_event(
            context, res_id=mes_id,
            res_type=constants.RES_TYPE_mes,
            res_state=constants.PENDING_CREATE,
            evt_type=constants.RES_EVT_CREATE,
            tstamp=mes_db[constants.RES_EVT_CREATED_FLD],
            details=evt_details)
        return self._make_mes_dict(mes_db)

    def create_mes_post(self, context, mes_id, mistral_obj,
            mead_dict, error_reason):
        LOG.debug('mes ID %s', mes_id)
        output = ast.literal_eval(mistral_obj.output)
        mgmt_urls = dict()
        mea_ids = dict()
        if len(output) > 0:
            for mead_name, mead_val in iteritems(mead_dict):
                for instance in mead_val['instances']:
                    if 'mgmt_url_' + instance in output:
                        mgmt_urls[instance] = ast.literal_eval(
                            output['mgmt_url_' + instance].strip())
                        mea_ids[instance] = output['mea_id_' + instance]
            mea_ids = str(mea_ids)
            mgmt_urls = str(mgmt_urls)

        if not mea_ids:
            mea_ids = None
        if not mgmt_urls:
            mgmt_urls = None
        status = constants.ACTIVE if mistral_obj.state == 'SUCCESS' \
            else constants.ERROR
        with context.session.begin(subtransactions=True):
            mes_db = self._get_resource(context, MES,
                                       mes_id)
            mes_db.update({'mea_ids': mea_ids})
            mes_db.update({'mgmt_urls': mgmt_urls})
            mes_db.update({'status': status})
            mes_db.update({'error_reason': error_reason})
            mes_db.update({'updated_at': timeutils.utcnow()})
            mes_dict = self._make_mes_dict(mes_db)
            self._cos_db_plg.create_event(
                context, res_id=mes_dict['id'],
                res_type=constants.RES_TYPE_mes,
                res_state=constants.RES_EVT_NA_STATE,
                evt_type=constants.RES_EVT_UPDATE,
                tstamp=mes_dict[constants.RES_EVT_UPDATED_FLD])
        return mes_dict

    # reference implementation. needs to be overrided by subclass
    def delete_mes(self, context, mes_id):
        with context.session.begin(subtransactions=True):
            mes_db = self._get_mes_db(
                context, mes_id, _ACTIVE_UPDATE_ERROR_DEAD,
                constants.PENDING_DELETE)
        deleted_mes_db = self._make_mes_dict(mes_db)
        self._cos_db_plg.create_event(
            context, res_id=mes_id,
            res_type=constants.RES_TYPE_mes,
            res_state=deleted_mes_db['status'],
            evt_type=constants.RES_EVT_DELETE,
            tstamp=timeutils.utcnow(), details="MES delete initiated")
        return deleted_mes_db

    def delete_mes_post(self, context, mes_id, mistral_obj,
                       error_reason, soft_delete=True):
        mes = self.get_mes(context, mes_id)
        mesd_id = mes.get('mesd_id')
        with context.session.begin(subtransactions=True):
            query = (
                self._model_query(context, MES).
                filter(MES.id == mes_id).
                filter(MES.status == constants.PENDING_DELETE))
            if mistral_obj and mistral_obj.state == 'ERROR':
                query.update({'status': constants.ERROR})
                self._cos_db_plg.create_event(
                    context, res_id=mes_id,
                    res_type=constants.RES_TYPE_mes,
                    res_state=constants.ERROR,
                    evt_type=constants.RES_EVT_DELETE,
                    tstamp=timeutils.utcnow(),
                    details="MES Delete ERROR")
            else:
                if soft_delete:
                    deleted_time_stamp = timeutils.utcnow()
                    query.update({'deleted_at': deleted_time_stamp})
                    self._cos_db_plg.create_event(
                        context, res_id=mes_id,
                        res_type=constants.RES_TYPE_mes,
                        res_state=constants.PENDING_DELETE,
                        evt_type=constants.RES_EVT_DELETE,
                        tstamp=deleted_time_stamp,
                        details="mes Delete Complete")
                else:
                    query.delete()
            template_db = self._get_resource(context, MESD, mesd_id)
            if template_db.get('template_source') == 'inline':
                self.delete_mesd(context, mesd_id)

    def get_mes(self, context, mes_id, fields=None):
        mes_db = self._get_resource(context, MES, mes_id)
        return self._make_mes_dict(mes_db)

    def get_mess(self, context, filters=None, fields=None):
        return self._get_collection(context, MES,
                                    self._make_mes_dict,
                                    filters=filters, fields=fields)
