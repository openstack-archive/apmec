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

"""mesd-table

Revision ID: 20f6a08b066e
Revises: 8206737b5c80
Create Date: 2018-06-13 20:36:59.470322

"""

# revision identifiers, used by Alembic.
revision = '20f6a08b066e'
down_revision = '8206737b5c80'

from alembic import op
import sqlalchemy as sa

from apmec.db import types


def upgrade(active_plugins=None, options=None):
   op.add_column('mesd',
                  sa.Column('mesd_mapping',
                           types.Json, nullable=True))
   op.add_column('mes',
                 sa.Column('mes_mapping',
                           types.Json, nullable=True))

   op.add_column('mes',
                 sa.Column('reused',
                           types.Json, nullable=True))