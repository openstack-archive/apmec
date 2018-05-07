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

===============================
Welcome to Apmec Documentation
===============================

Apmec is an OpenStack service for MEC Orchestration with a general purpose
MEA Manager to deploy and operate Virtual Network Functions (MEAs) and
Network Services on an MEC Platform. It is based on ETSI MANO Architectural
Framework.

Installation
============

For Apmec to work, the system consists of two parts, one is apmec system
and another is VIM systems. Apmec system can be installed
(here just some ways are listed):

* via devstack, which is usually used by developers
* via Apmec source code manually
* via Kolla installation


.. toctree::
   :maxdepth: 1

   install/kolla.rst
   install/devstack.rst
   install/manual_installation.rst

Target VIM installation
=======================

Most of time, the target VIM existed for Apmec to manage. This section shows
us how to prepare a target VIM for Apmec.

.. toctree::
   :maxdepth: 1

   install/openstack_vim_installation.rst


Getting Started
===============

.. toctree::
   :maxdepth: 1

   install/getting_started.rst
   install/deploy_openwrt.rst

Feature Documentation
=====================

.. toctree::
   :maxdepth: 1

   contributor/mead_template_description.rst
   contributor/monitor-api.rst
   contributor/mead_template_parameterization.rst
   contributor/event_logging.rst
   contributor/apmec_conductor.rst
   contributor/apmec_vim_monitoring.rst
   contributor/policy_actions_framework.rst
   contributor/encrypt_vim_auth_with_barbican.rst

User Guide
==========

.. toctree::
   :maxdepth: 1

   user/mem_usage_guide.rst
   user/multisite_vim_usage_guide.rst
   user/scale_usage_guide.rst
   user/alarm_monitoring_usage_guide.rst
   user/mesd_usage_guide.rst
   user/mea_component_usage_guide.rst
   user/enhanced_placement_awareness_usage_guide.rst
   reference/mistral_workflows_usage_guide.rst
   reference/block_storage_usage_guide.rst

API Documentation
=================

.. toctree::
   :maxdepth: 2

   contributor/api/mano_api.rst

Contributing to Apmec
======================

.. toctree::
   :maxdepth: 1

   contributor/dev-process.rst

Developer Info
==============

.. toctree::
   :maxdepth: 1

   contributor/development.environment.rst
   contributor/api/api_layer.rst
   contributor/api/api_extensions.rst
   contributor/apmec_functional_test.rst
   contributor/dashboards.rst

Project Info
============

* **Free software:** under the `Apache license <http://www.apache.org/licenses/LICENSE-2.0>`_
* **Apmec Service:** http://git.openstack.org/cgit/openstack/apmec
* **Apmec Client Library:** http://git.openstack.org/cgit/openstack/python-apmecclient
* **Apmec Service Bugs:** http://bugs.launchpad.net/apmec
* **Client Bugs:** https://bugs.launchpad.net/python-apmecclient
* **Blueprints:** https://blueprints.launchpad.net/apmec

Indices and tables
------------------

* :ref:`search`
* :ref:`modindex`
