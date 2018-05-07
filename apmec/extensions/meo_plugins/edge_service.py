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

import abc
import six

from apmec.common import exceptions
from apmec.services import service_base


@six.add_metaclass(abc.ABCMeta)
class MESPluginBase(service_base.MECPluginBase):

    @abc.abstractmethod
    def create_mesd(self, context, mesd):
        pass

    @abc.abstractmethod
    def delete_mesd(self, context, mesd_id):
        pass

    @abc.abstractmethod
    def get_mesd(self, context, mesd_id, fields=None):
        pass

    @abc.abstractmethod
    def get_mesds(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def create_mes(self, context, mes):
        pass

    @abc.abstractmethod
    def get_mess(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_mes(self, context, mes_id, fields=None):
        pass

    @abc.abstractmethod
    def delete_mes(self, context, mes_id):
        pass


class MESDNotFound(exceptions.NotFound):
    message = _('MESD %(mesd_id)s could not be found')


class MESNotFound(exceptions.NotFound):
    message = _('MES %(mes_id)s could not be found')
