# Copyright 2017 OpenStack Foundation
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

"""add_attributes_to_NANY

Revision ID: e8918cda6433
Revises: 000632983ada
Create Date: 2017-02-09 00:11:08.081746

"""

# revision identifiers, used by Alembic.
revision = 'e8918cda6433'
down_revision = '000632983ada'

from alembic import op
from apmec.db.types import Json
import sqlalchemy as sa


def upgrade(active_plugins=None, options=None):
    op.add_column('NANYs', sa.Column('attributes', Json))
