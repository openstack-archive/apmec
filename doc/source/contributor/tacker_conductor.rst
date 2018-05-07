..
      Copyright 2014-2015 OpenStack Foundation
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

================
Apmec conductor
================

Apmec conductor is a component which is used to communicate with other
components via message RPC. In the conductor, the RPC server sides can
access the apmec base on behalf of them.


To start
==============

Apmec conductor can be started via python console entry script
'apmec-conductor':

.. code-block:: console

   apmec-conductor --config-file /etc/apmec/apmec.conf

..

we can easily start many apmec-conductor instances with different 'host' value
in the configuration file:

.. code-block:: console

   test@ubuntu64:~/devstack$ grep 'host = secondinstance' /etc/apmec/apmec2.conf
   host = secondinstance

..

and then start the second instance:

.. code-block:: console

   apmec-conductor --config-file /etc/apmec/apmec2.conf

..

Rabbitmq queues
===============

Apmec conductor is listening on three queues:

.. code-block:: console

    test@ubuntu64:~/apmec$ sudo rabbitmqctl list_queues | grep CONDUCTOR
    APMEC_CONDUCTOR	0
    APMEC_CONDUCTOR.ubuntu64	0
    APMEC_CONDUCTOR_fanout_0ea005c0b666488485a7b3689eb70168	0

..

But only APMEC_CONDUCTOR queue without host suffix is used.
