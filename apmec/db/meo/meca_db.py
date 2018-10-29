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
from apmec.plugins.common import constants

LOG = logging.getLogger(__name__)
_ACTIVE_UPDATE = (constants.ACTIVE, constants.PENDING_UPDATE)
_ACTIVE_UPDATE_ERROR_DEAD = (
    constants.PENDING_CREATE, constants.ACTIVE, constants.PENDING_UPDATE,
    constants.ERROR, constants.DEAD)
CREATE_STATES = (constants.PENDING_CREATE, constants.DEAD)


###########################################################################
# db tables

class MECAD(model_base.BASE, models_v1.HasId, models_v1.HasTenant,
        models_v1.Audit):
    """Represents MECAD to create MECA."""

    __tablename__ = 'mecad'
    # Descriptive name
    name = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text)
    meads = sa.Column(types.Json, nullable=True)

    # Mecad template source - onboarded
    template_source = sa.Column(sa.String(255), server_default='onboarded')

    # (key, value) pair to spin up
    attributes = orm.relationship('MECADAttribute',
                                  backref='mecad')

    __table_args__ = (
        schema.UniqueConstraint(
            "tenant_id",
            "name",
            name="uniq_mecad0tenant_id0name"),
    )


class MECADAttribute(model_base.BASE, models_v1.HasId):
    """Represents attributes necessary for creation of meca in (key, value) pair

    """

    __tablename__ = 'mecad_attribute'
    mecad_id = sa.Column(types.Uuid, sa.ForeignKey('mecad.id'),
            nullable=False)
    key = sa.Column(sa.String(255), nullable=False)
    value = sa.Column(sa.TEXT(65535), nullable=True)


class MECA(model_base.BASE, models_v1.HasId, models_v1.HasTenant,
        models_v1.Audit):
    """Represents network services that deploys services.

    """

    __tablename__ = 'meca'
    mecad_id = sa.Column(types.Uuid, sa.ForeignKey('mecad.id'))
    mecad = orm.relationship('MECAD')

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
            name="uniq_meca0tenant_id0name"),
    )


class MECAPluginDb(meo.MECAPluginBase, db_base.CommonDbMixin):

    def __init__(self):
        super(MECAPluginDb, self).__init__()
        self._cos_db_plg = common_services_db_plugin.CommonServicesPluginDb()

    def _get_resource(self, context, model, id):
        try:
            return self._get_by_id(context, model, id)
        except orm_exc.NoResultFound:
            if issubclass(model, MECAD):
                raise meo.MECADNotFound(mecad_id=id)
            if issubclass(model, MECA):
                raise meo.MECANotFound(meca_id=id)
            else:
                raise

    def _get_meca_db(self, context, meca_id, current_statuses, new_status):
        try:
            meca_db = (
                self._model_query(context, MECA).
                filter(MECA.id == meca_id).
                filter(MECA.status.in_(current_statuses)).
                with_lockmode('update').one())
        except orm_exc.NoResultFound:
            raise meo.MECANotFound(meca_id=meca_id)
        meca_db.update({'status': new_status})
        return meca_db

    def _make_attributes_dict(self, attributes_db):
        return dict((attr.key, attr.value) for attr in attributes_db)

    def _make_mecad_dict(self, mecad, fields=None):
        res = {
            'attributes': self._make_attributes_dict(mecad['attributes']),
        }
        key_list = ('id', 'tenant_id', 'name', 'description',
                    'created_at', 'updated_at', 'meads', 'template_source')
        res.update((key, mecad[key]) for key in key_list)
        return self._fields(res, fields)

    def _make_dev_attrs_dict(self, dev_attrs_db):
        return dict((arg.key, arg.value) for arg in dev_attrs_db)

    def _make_meca_dict(self, meca_db, fields=None):
        LOG.debug('meca_db %s', meca_db)
        res = {}
        key_list = ('id', 'tenant_id', 'mecad_id', 'name', 'description',
                    'mea_ids', 'status', 'mgmt_urls', 'error_reason',
                    'vim_id', 'created_at', 'updated_at')
        res.update((key, meca_db[key]) for key in key_list)
        return self._fields(res, fields)

    def create_mecad(self, context, mecad):
        meads = mecad['meads']
        mecad = mecad['mecad']
        LOG.debug('mecad %s', mecad)
        tenant_id = self._get_tenant_id_for_create(context, mecad)
        template_source = mecad.get('template_source')

        try:
            with context.session.begin(subtransactions=True):
                mecad_id = uuidutils.generate_uuid()
                mecad_db = MECAD(
                    id=mecad_id,
                    tenant_id=tenant_id,
                    name=mecad.get('name'),
                    meads=meads,
                    description=mecad.get('description'),
                    deleted_at=datetime.min,
                    template_source=template_source)
                context.session.add(mecad_db)
                for (key, value) in mecad.get('attributes', {}).items():
                    attribute_db = MECADAttribute(
                        id=uuidutils.generate_uuid(),
                        mecad_id=mecad_id,
                        key=key,
                        value=value)
                    context.session.add(attribute_db)
        except DBDuplicateEntry as e:
            raise exceptions.DuplicateEntity(
                _type="mecad",
                entry=e.columns)
        LOG.debug('mecad_db %(mecad_db)s %(attributes)s ',
                  {'mecad_db': mecad_db,
                   'attributes': mecad_db.attributes})
        mecad_dict = self._make_mecad_dict(mecad_db)
        LOG.debug('mecad_dict %s', mecad_dict)
        self._cos_db_plg.create_event(
            context, res_id=mecad_dict['id'],
            res_type=constants.RES_TYPE_MECAD,
            res_state=constants.RES_EVT_ONBOARDED,
            evt_type=constants.RES_EVT_CREATE,
            tstamp=mecad_dict[constants.RES_EVT_CREATED_FLD])
        return mecad_dict

    def delete_mecad(self,
            context,
            mecad_id,
            soft_delete=True):
        with context.session.begin(subtransactions=True):
            mecas_db = context.session.query(MECA).filter_by(
                mecad_id=mecad_id).first()
            if mecas_db is not None and mecas_db.deleted_at is None:
                raise meo.MECADInUse(mecad_id=mecad_id)

            mecad_db = self._get_resource(context, MECAD,
                                        mecad_id)
            if soft_delete:
                mecad_db.update({'deleted_at': timeutils.utcnow()})
                self._cos_db_plg.create_event(
                    context, res_id=mecad_db['id'],
                    res_type=constants.RES_TYPE_MECAD,
                    res_state=constants.RES_EVT_NA_STATE,
                    evt_type=constants.RES_EVT_DELETE,
                    tstamp=mecad_db[constants.RES_EVT_DELETED_FLD])
            else:
                context.session.query(MECADAttribute).filter_by(
                    mecad_id=mecad_id).delete()
                context.session.delete(mecad_db)

    def get_mecad(self, context, mecad_id, fields=None):
        mecad_db = self._get_resource(context, MECAD, mecad_id)
        return self._make_mecad_dict(mecad_db)

    def get_mecads(self, context, filters, fields=None):
        if ('template_source' in filters) and \
                (filters['template_source'][0] == 'all'):
            filters.pop('template_source')
        return self._get_collection(context, MECAD,
                                    self._make_mecad_dict,
                                    filters=filters, fields=fields)

    # reference implementation. needs to be overrided by subclass
    def create_meca(self, context, meca):
        LOG.debug('meca %s', meca)
        meca = meca['meca']
        tenant_id = self._get_tenant_id_for_create(context, meca)
        mecad_id = meca['mecad_id']
        vim_id = meca['vim_id']
        name = meca.get('name')
        meca_id = uuidutils.generate_uuid()
        try:
            with context.session.begin(subtransactions=True):
                mecad_db = self._get_resource(context, MECAD,
                                            mecad_id)
                meca_db = MECA(id=meca_id,
                           tenant_id=tenant_id,
                           name=name,
                           description=mecad_db.description,
                           mea_ids=None,
                           status=constants.PENDING_CREATE,
                           mgmt_urls=None,
                           mecad_id=mecad_id,
                           vim_id=vim_id,
                           error_reason=None,
                           deleted_at=datetime.min)
                context.session.add(meca_db)
        except DBDuplicateEntry as e:
            raise exceptions.DuplicateEntity(
                _type="meca",
                entry=e.columns)
        evt_details = "MECA UUID assigned."
        self._cos_db_plg.create_event(
            context, res_id=meca_id,
            res_type=constants.RES_TYPE_meca,
            res_state=constants.PENDING_CREATE,
            evt_type=constants.RES_EVT_CREATE,
            tstamp=meca_db[constants.RES_EVT_CREATED_FLD],
            details=evt_details)
        return self._make_meca_dict(meca_db)

    def create_meca_post(self, context, meca_id, mistral_obj,
            mead_dict, error_reason):
        LOG.debug('meca ID %s', meca_id)
        output = ast.literal_eval(mistral_obj.output)
        mgmt_urls = dict()
        mea_ids = dict()
        if len(output) > 0:
            for mead_name, mead_val in iteritems(mead_dict):
                for instance in mead_val['instances']:
                    if 'mgmt_url_' + instance in output:
                        mgmt_url_dict =\
                            ast.literal_eval(
                                output['mgmt_url_' + instance].strip())
                        mgmt_urls[instance] = mgmt_url_dict.values()
                        mea_ids[instance] = list()
                        mea_ids[instance].append(output['mea_id_' + instance])
            mea_ids = str(mea_ids)
            mgmt_urls = str(mgmt_urls)

        if not mea_ids:
            mea_ids = None
        if not mgmt_urls:
            mgmt_urls = None
        status = constants.ACTIVE if mistral_obj.state == 'SUCCESS' \
            else constants.ERROR
        with context.session.begin(subtransactions=True):
            meca_db = self._get_resource(context, MECA,
                                       meca_id)
            meca_db.update({'mea_ids': mea_ids})
            meca_db.update({'mgmt_urls': mgmt_urls})
            meca_db.update({'status': status})
            meca_db.update({'error_reason': error_reason})
            meca_db.update({'updated_at': timeutils.utcnow()})
            meca_dict = self._make_meca_dict(meca_db)
            self._cos_db_plg.create_event(
                context, res_id=meca_dict['id'],
                res_type=constants.RES_TYPE_meca,
                res_state=constants.RES_EVT_NA_STATE,
                evt_type=constants.RES_EVT_UPDATE,
                tstamp=meca_dict[constants.RES_EVT_UPDATED_FLD])
        return meca_dict

    # reference implementation. needs to be overrided by subclass
    def delete_meca(self, context, meca_id):
        with context.session.begin(subtransactions=True):
            meca_db = self._get_meca_db(
                context, meca_id, _ACTIVE_UPDATE_ERROR_DEAD,
                constants.PENDING_DELETE)
        deleted_meca_db = self._make_meca_dict(meca_db)
        self._cos_db_plg.create_event(
            context, res_id=meca_id,
            res_type=constants.RES_TYPE_meca,
            res_state=deleted_meca_db['status'],
            evt_type=constants.RES_EVT_DELETE,
            tstamp=timeutils.utcnow(), details="MECA delete initiated")
        return deleted_meca_db

    def delete_meca_post(self, context, meca_id, mistral_obj,
                       error_reason, soft_delete=True):
        meca = self.get_meca(context, meca_id)
        mecad_id = meca.get('mecad_id')
        with context.session.begin(subtransactions=True):
            query = (
                self._model_query(context, MECA).
                filter(MECA.id == meca_id).
                filter(MECA.status == constants.PENDING_DELETE))
            if mistral_obj and mistral_obj.state == 'ERROR':
                query.update({'status': constants.ERROR})
                self._cos_db_plg.create_event(
                    context, res_id=meca_id,
                    res_type=constants.RES_TYPE_meca,
                    res_state=constants.ERROR,
                    evt_type=constants.RES_EVT_DELETE,
                    tstamp=timeutils.utcnow(),
                    details="MECA Delete ERROR")
            else:
                if soft_delete:
                    deleted_time_stamp = timeutils.utcnow()
                    query.update({'deleted_at': deleted_time_stamp})
                    self._cos_db_plg.create_event(
                        context, res_id=meca_id,
                        res_type=constants.RES_TYPE_meca,
                        res_state=constants.PENDING_DELETE,
                        evt_type=constants.RES_EVT_DELETE,
                        tstamp=deleted_time_stamp,
                        details="meca Delete Complete")
                else:
                    query.delete()
            template_db = self._get_resource(context, MECAD, mecad_id)
            if template_db.get('template_source') == 'inline':
                self.delete_mecad(context, mecad_id)

    def get_meca(self, context, meca_id, fields=None):
        meca_db = self._get_resource(context, MECA, meca_id)
        return self._make_meca_dict(meca_db)

    def get_mecas(self, context, filters=None, fields=None):
        return self._get_collection(context, MECA,
                                    self._make_meca_dict,
                                    filters=filters, fields=fields)

    def _update_meca_pre(self, context, meca_id):
        with context.session.begin(subtransactions=True):
            meca_db = self._get_meca_db(
                context, meca_id, _ACTIVE_UPDATE,
                constants.PENDING_UPDATE)
            return self._make_meca_dict(meca_db)

    def _update_meca_post(self, context, meca_id, mistral_obj,
            mead_dict, error_reason):
        output = ast.literal_eval(mistral_obj.output)
        new_mgmt_urls = dict()
        new_mea_ids = dict()
        if len(output) > 0:
            for mead_name, mead_val in iteritems(mead_dict):
                for instance in mead_val['instances']:
                    if 'mgmt_url_' + instance in output:
                        mgmt_url_dict = ast.literal_eval(
                            output['mgmt_url_' + instance].strip())
                        new_mgmt_urls[instance] = mgmt_url_dict.values()
                        new_mea_ids[instance] = output['mea_id_' + instance]

        if not new_mea_ids:
            new_mea_ids = None
        if not new_mgmt_urls:
            new_mgmt_urls = None
        status = constants.ACTIVE if mistral_obj.state == 'SUCCESS' \
            else constants.ERROR
        with context.session.begin(subtransactions=True):
            meca_db = self._get_resource(context, MECA, meca_id)
            mgmt_urls = ast.literal_eval(meca_db.mgmt_urls)
            for mea_name, mgmt_dict in mgmt_urls.items():
                for new_mea_name, new_mgmt_dict in new_mgmt_urls.items():
                    if new_mea_name == mea_name:
                        extra_mgmt = new_mgmt_urls.pop(new_mea_name)
                        mgmt_urls[mea_name].extend(extra_mgmt)

            mgmt_urls.update(new_mgmt_urls)
            mgmt_urls = str(mgmt_urls)
            mea_ids = ast.literal_eval(meca_db.mea_ids)
            for mea_name, mea_id_list in mea_ids.items():
                for new_mea_name, new_mead_id_list in new_mea_ids.items():
                    if new_mea_name == mea_name:
                        extra_id = new_mea_ids.pop(new_mea_name)
                        mea_ids[mea_name].append(extra_id)
            mea_ids.update(new_mea_ids)
            mea_ids = str(mea_ids)
            meca_db.update({'mea_ids': mea_ids})
            meca_db.update({'mgmt_urls': mgmt_urls})
            meca_db.update({'status': status})
            meca_db.update({'error_reason': error_reason})
            meca_db.update({'updated_at': timeutils.utcnow()})
            meca_dict = self._make_meca_dict(meca_db)
        return meca_dict

    def _update_meca_status(self, context, meca_id, new_status):
        with context.session.begin(subtransactions=True):
            meca_db = self._get_meca_db(
                context, meca_id, _ACTIVE_UPDATE, new_status)
            return self._make_meca_dict(meca_db)

    def update_meca(self, context, meca_id, meca):
        meca_dict = self._update_meca_pre(context, meca_id)
        self._update_meca_post(context, meca_id,
                               constants.ACTIVE, meca_dict, None)
