..
  Licensed under the Apache License, Version 2.0 (the "License"); you may
  not use this file except in compliance with the License. You may obtain
  a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
  License for the specific language governing permissions and limitations
  under the License.

.. _ref-scale:

===========
MEA scaling
===========

MEA resources in terms of CPU core and memory are hardcoded in MEAD template
through image flavor settings. This result in either provisioning MEA for
typical usage or for maximum usage. The former leads to service disruption
when load exceeds provisioned capacity. And the later leads to underutilized
resources and waste during normal system load. So apmec provides a
way to seamlessly scale the number of MEAs on demand either manually or
automatically.


TOSCA schema for scaling policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apmec defines TOSCA schema for the scaling policy as given below:

.. code-block:: yaml

  tosca.policies.apmec.Scaling:
    derived_from: tosca.policies.Scaling
    description: Defines policy for scaling the given targets.
    properties:
      increment:
        type: integer
        required: true
        description: Number of nodes to add or remove during the scale out/in.
      targets:
        type: list
        entry_schema:
          type: string
        required: true
        description: List of Scaling nodes.
      min_instances:
        type: integer
        required: true
        description: Minimum number of instances to scale in.
      max_instances:
        type: integer
        required: true
        description: Maximum number of instances to scale out.
      default_instances:
        type: integer
        required: true
        description: Initial number of instances.
      cooldown:
        type: integer
        required: false
        default: 120
        description: Wait time (in seconds) between consecutive scaling
        operations. During the cooldown period, scaling action will be ignored


Sample TOSCA with scaling policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Following TOSCA snippet shows the scaling policy used in MEAD, in which vdu1
and vdu2 are already defined VDUs.

.. code-block:: yaml

     policies:

        sp1:

          type: tosca.policies.apmec.Scaling

          description: Simple VDU scaling

          properties:
             min_instances: 1

             max_instances: 3

             default_instances: 2

             increment: 1

             targets: [vdu1, vdu2]


Deploying scaling TOSCA template using Apmec
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once OpenStack/Devstack along with Apmec has been successfully installed,
deploy a sample scaling template from location given
below:
https://github.com/openstack/apmec/tree/master/samples/tosca-templates/mead

Refer the 'Getting Started' link below on how to create a MEAD and deploy a
MEA:
https://docs.openstack.org/apmec/latest/install/getting_started.html


How to scale MEA using CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~

Apmec provides following CLI for scaling.

.. code-block::console

**apmec mea-scale --mea-id <mea-id>**
                  **--mea-name <mea name>**
                  **--scaling-policy-name <policy name>**
                  **--scaling-type <type>**

Here,

* scaling-policy-name - Policy name defined in scaling MEAD
* scaling-type - in or out
* mea-id - scaling MEA id
* mea-name - scaling MEA name

For example, to scale-out policy 'sp1' defined above, this cli could be used
as below:

.. code-block::console

**apmec mea-scale --mea-name sample-mea**
                  **--scaling-policy-name sp1**
                  **--scaling-type out**

How to scale MEA using REST API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apmec provides following REST API for scaling.

**POST on v1.0/meas/<mea-id>/actions**

with body

.. code-block::json

**{"scale": { "type": "<type>", "policy" : "<scaling-policy-name>"}}**

Here,

* scaling-policy-name - Policy name defined in scaling MEAD
* scaling-type - in or out
* mea-id - scaling MEA id

Response http status codes:

* 202 - Accepted the request for doing the scaling operation
* 404 - Bad request, if given scaling-policy-name and type are invalid
* 500 - Internal server error, on scaling operation failed due to an error
* 401 - Unauthorized

MEA state transitions during scaling operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
During the scaling operation, the MEA will be moving in below state
transformations:

* **ACTIVE -> PENDING_SCALE_IN -> ACTIVE**
* **ACTIVE -> PENDING_SCALE_IN -> ERROR**
* **ACTIVE -> PENDING_SCALE_OUT -> ACTIVE**
* **ACTIVE -> PENDING_SCALE_OUT -> ERROR**


Limitations
~~~~~~~~~~~

Following features are not supported with scaling:

* Auto-scaling feature is supported only with alarm monitors and it does
  not work with other monitors such as ping, http_ping.
* When MEA is modelled with scaling requirement in MEAD, any config
  management requirement in MEAD is not supported.
* Scaling feature does not support to selectively choose the VDU as part
  of scaling.
