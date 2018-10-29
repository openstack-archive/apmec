# Copyright 2018 OpenStack Foundation
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

"""meca-table

Revision ID: 8206737b5c80
Revises: e9a1e47fb0b5
Create Date: 2018-06-08 15:58:43.286238

"""

# revision identifiers, used by Alembic.
revision = '8206737b5c80'
down_revision = 'e9a1e47fb0b5'

from alembic import op
import sqlalchemy as sa


from apmec.db import types


def upgrade(active_plugins=None, options=None):
    op.create_table('mecad',
                    sa.Column('tenant_id', sa.String(length=64), nullable=False),
                    sa.Column('id', types.Uuid(length=36), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('meads', types.Json, nullable=True),
                    sa.Column('template_source', sa.String(length=255), server_default='onboarded'),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB'
                    )
    op.create_table('meca',
                    sa.Column('tenant_id', sa.String(length=64), nullable=False),
                    sa.Column('id', types.Uuid(length=36), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.Column('mecad_id', types.Uuid(length=36), nullable=True),
                    sa.Column('vim_id', sa.String(length=64), nullable=False),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('mea_ids', sa.TEXT(length=65535), nullable=True),
                    sa.Column('mgmt_urls', sa.TEXT(length=65535), nullable=True),
                    sa.Column('status', sa.String(length=64), nullable=False),
                    sa.Column('error_reason', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['mecad_id'], ['mecad.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB'
                    )
    op.create_table('mecad_attribute',
                    sa.Column('id', types.Uuid(length=36), nullable=False),
                    sa.Column('mecad_id', types.Uuid(length=36), nullable=False),
                    sa.Column('key', sa.String(length=255), nullable=False),
                    sa.Column('value', sa.TEXT(length=65535), nullable=True),
                    sa.ForeignKeyConstraint(['mecad_id'], ['mecad.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB'
                    )
