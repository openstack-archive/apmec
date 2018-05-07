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

.. _ref-mistral:

============================
Mistral workflows for Apmec
============================

OpenStack Mistral already integrated with Apmec. The Tenant User or Operator
can make use of apmec actions to create custom Mistral Workflows. This
document describes the usage of Mistral CLI to validate, create and executing
Apmec workflows.


References
~~~~~~~~~~

- `Mistral workflow samples   <https://github.com/openstack/apmec/tree/master/samples/mistral/workflows>`_.
- `Mistral Client / CLI Guide <https://docs.openstack.org/mistral/latest/install/mistralclient_guide.html>`_.

Workflow definition file validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Validate workflow definition files before registering with Mistral.

::

  usage: mistral workflow-validate <definition>

::

  $ mistral workflow-validate create_mea.yaml

  +-------+-------+
  | Field | Value |
  +-------+-------+
  | Valid | True  |
  | Error | None  |
  +-------+-------+

  $ mistral workflow-validate create_mead.yaml

  +-------+-------+
  | Field | Value |
  +-------+-------+
  | Valid | True  |
  | Error | None  |
  +-------+-------+

  $ mistral workflow-validate delete_mea.yaml

  +-------+-------+
  | Field | Value |
  +-------+-------+
  | Valid | True  |
  | Error | None  |
  +-------+-------+

  $ mistral workflow-validate delete_mead.yaml

  +-------+-------+
  | Field | Value |
  +-------+-------+
  | Valid | True  |
  | Error | None  |
  +-------+-------+

Registering Apmec workflows with Mistral
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create std.create_mea, std.create_mead, std.delete_mead and
std.delete_mea workflows in Mistral.

::

  usage: mistral workflow-create <definition> --public

::

  $ mistral workflow-create create_mea.yaml --public

  +--------------------------------------+----------------+----------------------------------+--------+-------+----------------------------+------------+
  | ID                                   | Name           | Project ID                       | Tags   | Input | Created at                 | Updated at |
  +--------------------------------------+----------------+----------------------------------+--------+-------+----------------------------+------------+
  | 445e165a-3654-4996-aad4-c6fea65e95d5 | std.create_mea | bde60e557de840a8a837733aaa96e42e | <none> | body  | 2016-07-29 15:08:45.585192 | None       |
  +--------------------------------------+----------------+----------------------------------+--------+-------+----------------------------+------------+

  $ mistral workflow-create create_mead.yaml --public

  +--------------------------------------+-----------------+----------------------------------+--------+-------+----------------------------+------------+
  | ID                                   | Name            | Project ID                       | Tags   | Input | Created at                 | Updated at |
  +--------------------------------------+-----------------+----------------------------------+--------+-------+----------------------------+------------+
  | 926caa3e-ee59-4ca0-ac1b-cae03538e389 | std.create_mead | bde60e557de840a8a837733aaa96e42e | <none> | body  | 2016-07-29 15:08:54.933874 | None       |
  +--------------------------------------+-----------------+----------------------------------+--------+-------+----------------------------+------------+

  $ mistral workflow-create delete_mead.yaml --public

  +--------------------------------------+-----------------+----------------------------------+--------+---------+----------------------------+------------+
  | ID                                   | Name            | Project ID                       | Tags   | Input   | Created at                 | Updated at |
  +--------------------------------------+-----------------+----------------------------------+--------+---------+----------------------------+------------+
  | f15b7402-ce31-4369-98d4-818125191564 | std.delete_mead | bde60e557de840a8a837733aaa96e42e | <none> | mead_id | 2016-08-14 20:01:00.135104 | None       |
  +--------------------------------------+-----------------+----------------------------------+--------+---------+----------------------------+------------+

  $ mistral workflow-create delete_mea.yaml --public
  +--------------------------------------+----------------+----------------------------------+--------+--------+----------------------------+------------+
  | ID                                   | Name           | Project ID                       | Tags   | Input  | Created at                 | Updated at |
  +--------------------------------------+----------------+----------------------------------+--------+--------+----------------------------+------------+
  | d6451b4e-6448-4a26-aa33-ac5e18c7a412 | std.delete_mea | bde60e557de840a8a837733aaa96e42e | <none> | mea_id | 2016-08-14 20:01:08.088654 | None       |
  +--------------------------------------+----------------+----------------------------------+--------+--------+----------------------------+------------+



MEAD resource creation with std.create_mead workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To create MEAD apmec resource based on the MEAD workflow input file.

Create new execution for MEAD creation.

::

  usage: mistral execution-create <workflow_name> [<workflow_input>] [<params>]

::

  $ mistral execution-create std.create_mead create_mead.json

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 31f086aa-a3c9-4f44-b8b2-bec560e32653 |
  | Workflow ID       | 926caa3e-ee59-4ca0-ac1b-cae03538e389 |
  | Workflow name     | std.create_mead                      |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | RUNNING                              |
  | State info        | None                                 |
  | Created at        | 2016-07-29 15:11:19.485722           |
  | Updated at        | 2016-07-29 15:11:19.491694           |
  +-------------------+--------------------------------------+

Gather execution details based on execution id.

::

  usage: mistral execution-get <id>

::

  $mistral execution-get 31f086aa-a3c9-4f44-b8b2-bec560e32653

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 31f086aa-a3c9-4f44-b8b2-bec560e32653 |
  | Workflow ID       | 926caa3e-ee59-4ca0-ac1b-cae03538e389 |
  | Workflow name     | std.create_mead                      |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | SUCCESS                              |
  | State info        | None                                 |
  | Created at        | 2016-07-29 15:11:19                  |
  | Updated at        | 2016-07-29 15:11:21                  |
  +-------------------+--------------------------------------+

.. note:: Wait until execution state become as SUCCESS.

Gather MEAD ID from execution output data.

::

   usage: mistral execution-get-output <id>

::

  $ mistral execution-get-output 31f086aa-a3c9-4f44-b8b2-bec560e32653

  Response:

  {
    "mead_id": "fb164b77-5e24-402d-b5f4-c6596352cabe"
  }

Verify MEAD details using apmec CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ apmec mead-show "fb164b77-5e24-402d-b5f4-c6596352cabe"

  +---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
  | Field         | Value                                                                                                                                                                     |
  +---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
  | attributes    | {"mead": "tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0\n\ndescription: Demo example\n\nmetadata:\n  template_name: sample-tosca-                         |
  |               | mead\n\ntopology_template:\n  node_templates:\n    VDU1:\n      type: tosca.nodes.mec.VDU.Apmec\n      properties:\n        image: cirros-0.3.5-x86_64-disk\n             |
  |               | flavor: m1.tiny\n        availability_zone: nova\n        mgmt_driver: noop\n        config: |\n          param0: key1\n          param1: key2\n\n    CP1:\n      type:   |
  |               | tosca.nodes.mec.CP.Apmec\n      properties:\n        management: true\n        anti_spoofing_protection: false\n      requirements:\n        - virtualLink:\n            |
  |               | node: VL1\n        - virtualBinding:\n            node: VDU1\n\n    CP2:\n      type: tosca.nodes.mec.CP.Apmec\n      properties:\n        anti_spoofing_protection:     |
  |               | false\n      requirements:\n        - virtualLink:\n            node: VL2\n        - virtualBinding:\n            node: VDU1\n\n    CP3:\n      type:                     |
  |               | tosca.nodes.mec.CP.Apmec\n      properties:\n        anti_spoofing_protection: false\n      requirements:\n        - virtualLink:\n            node: VL3\n        -      |
  |               | virtualBinding:\n            node: VDU1\n\n    VL1:\n      type: tosca.nodes.mec.VL\n      properties:\n        network_name: net_mgmt\n        vendor: Apmec\n\n        |
  |               | VL2:\n      type: tosca.nodes.mec.VL\n      properties:\n        network_name: net0\n        vendor: Apmec\n\n    VL3:\n      type: tosca.nodes.mec.VL\n                 |
  |               | properties:\n        network_name: net1\n        vendor: Apmec\n"}                                                                                                       |
  | description   | Demo example                                                                                                                                                              |
  | id            | fb164b77-5e24-402d-b5f4-c6596352cabe                                                                                                                                      |
  | infra_driver  | openstack                                                                                                                                                                      |
  | mgmt_driver   | noop                                                                                                                                                                      |
  | name          | apmec-create-mead                                                                                                                                                        |
  | service_types | {"service_type": "mead", "id": "db7c5077-7bbf-4bd3-87d5-e3c52daba255"}                                                                                                    |
  | tenant_id     | bde60e557de840a8a837733aaa96e42e                                                                                                                                          |
  +---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

MEA resource creation with std.create_mea workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Update the mead_id from the output of above execution in create_mea.json

Create new execution for MEA creation.

::

  $ mistral execution-create std.create_mea create_mea.json

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 3bf2051b-ac2e-433b-8f18-23f57f32f184 |
  | Workflow ID       | 445e165a-3654-4996-aad4-c6fea65e95d5 |
  | Workflow name     | std.create_mea                       |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | RUNNING                              |
  | State info        | None                                 |
  | Created at        | 2016-07-29 15:16:13.066555           |
  | Updated at        | 2016-07-29 15:16:13.072436           |
  +-------------------+--------------------------------------+

Gather execution details based on execution id.

::

  $ mistral execution-get 3bf2051b-ac2e-433b-8f18-23f57f32f184

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 3bf2051b-ac2e-433b-8f18-23f57f32f184 |
  | Workflow ID       | 445e165a-3654-4996-aad4-c6fea65e95d5 |
  | Workflow name     | std.create_mea                       |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | SUCCESS                              |
  | State info        | None                                 |
  | Created at        | 2016-07-29 15:16:13                  |
  | Updated at        | 2016-07-29 15:16:45                  |
  +-------------------+--------------------------------------+

Gather MEA ID from execution output data.

::

  $ mistral execution-get-output 3bf2051b-ac2e-433b-8f18-23f57f32f184

  Response:

  {
    "status": "ACTIVE",
    "mgmt_url": "{\"VDU1\": \"192.168.120.7\"}",
    "vim_id": "22ac5ce6-1415-460c-badf-40ffc5091f94",
    "mea_id": "1c349534-a539-4d5a-b854-033f98036cd5"
  }

Verify MEA details using apmec CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

  $ apmec mea-show "1c349534-a539-4d5a-b854-033f98036cd5"

  +----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
  | Field          | Value                                                                                                                                                                 |
  +----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
  | attributes     | {"heat_template": "heat_template_version: 2013-05-23\ndescription: 'Demo example\n\n  '\nparameters: {}\nresources:\n  VDU1:\n    type: OS::Nova::Server\n            |
  |                | properties:\n      availability_zone: nova\n      config_drive: false\n      flavor: m1.tiny\n      image: cirros-0.3.5-x86_64-disk\n      networks:\n      - port:\n  |
  |                | get_resource: CP1\n      - port:\n          get_resource: CP2\n      - port:\n          get_resource: CP3\n      user_data_format: SOFTWARE_CONFIG\n  CP1:\n    type: |
  |                | OS::Neutron::Port\n    properties:\n      network: net_mgmt\n      port_security_enabled: false\n  CP2:\n    type: OS::Neutron::Port\n    properties:\n      network: |
  |                | net0\n      port_security_enabled: false\n  CP3:\n    type: OS::Neutron::Port\n    properties:\n      network: net1\n      port_security_enabled: false\noutputs:\n   |
  |                | mgmt_ip-VDU1:\n    value:\n      get_attr: [CP1, fixed_ips, 0, ip_address]\n", "monitoring_policy": "{\"vdus\": {}}"}                                                 |
  | description    | Demo example                                                                                                                                                          |
  | error_reason   |                                                                                                                                                                       |
  | id             | 1c349534-a539-4d5a-b854-033f98036cd5                                                                                                                                  |
  | instance_id    | 771c53df-9f41-454c-a719-7eccd3a4eba9                                                                                                                                  |
  | mgmt_url       | {"VDU1": "192.168.120.7"}                                                                                                                                             |
  | name           | apmec-create-mea                                                                                                                                                     |
  | placement_attr | {"vim_name": "VIM0"}                                                                                                                                                  |
  | status         | ACTIVE                                                                                                                                                                |
  | tenant_id      | bde60e557de840a8a837733aaa96e42e                                                                                                                                      |
  | vim_id         | 22ac5ce6-1415-460c-badf-40ffc5091f94                                                                                                                                  |
  +----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

MEA resource deletion with std.delete_mea workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Update the mea_id from the output of above execution in delete_mea.json

Create new execution for MEA deletion.

::

  $ mistral execution-create std.delete_mea delete_mea.json

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 677c7bab-18ee-4a34-b1e6-a305e98ba887 |
  | Workflow ID       | d6451b4e-6448-4a26-aa33-ac5e18c7a412 |
  | Workflow name     | std.delete_mea                       |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | RUNNING                              |
  | State info        | None                                 |
  | Created at        | 2016-08-14 20:48:00.333116           |
  | Updated at        | 2016-08-14 20:48:00.340124           |
  +-------------------+--------------------------------------+

Gather execution details based on execution id.

::

  $ mistral execution-get 677c7bab-18ee-4a34-b1e6-a305e98ba887

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 677c7bab-18ee-4a34-b1e6-a305e98ba887 |
  | Workflow ID       | d6451b4e-6448-4a26-aa33-ac5e18c7a412 |
  | Workflow name     | std.delete_mea                       |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | SUCCESS                              |
  | State info        | None                                 |
  | Created at        | 2016-08-14 20:48:00                  |
  | Updated at        | 2016-08-14 20:48:03                  |
  +-------------------+--------------------------------------+


Gather execution output data from execution id.

::

  $ mistral execution-get-output 677c7bab-18ee-4a34-b1e6-a305e98ba887

  Response:

  {
    "openstack": {
        "project_name": "demo",
        "user_id": "f39a28fa574848dfa950b50329c1309b",
        "roles": [
            "anotherrole",
            "Member"
        ],
        "auth_uri": "http://192.168.122.250:5000/v3",
        "auth_cacert": null,
        "auth_token": "2871049fae3643ca84f44f7e17f809a0",
        "is_trust_scoped": false,
        "service_catalog": "[{\"endpoints\": [{\"adminURL\": \"http://192.168.122.250/identity_v2_admin\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250/identity\", \"publicURL\": \"http://192.168.122.250/identity\"}], \"type\": \"identity\", \"name\": \"keystone\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9292\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9292\", \"publicURL\": \"http://192.168.122.250:9292\"}], \"type\": \"image\", \"name\": \"glance\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8774/v2.1\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8774/v2.1\", \"publicURL\": \"http://192.168.122.250:8774/v2.1\"}], \"type\": \"compute\", \"name\": \"nova\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8776/v2/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8776/v2/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8776/v2/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"volumev2\", \"name\": \"cinderv2\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8776/v1/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8776/v1/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8776/v1/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"volume\", \"name\": \"cinder\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9494\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9494\", \"publicURL\": \"http://192.168.122.250:9494\"}], \"type\": \"artifact\", \"name\": \"glare\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8004/v1/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8004/v1/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8004/v1/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"orchestration\", \"name\": \"heat\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8774/v2/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8774/v2/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8774/v2/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"compute_legacy\", \"name\": \"nova_legacy\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9896/\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9896/\", \"publicURL\": \"http://192.168.122.250:9896/\"}], \"type\": \"mec-orchestration\", \"name\": \"apmec\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8989/v2\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8989/v2\", \"publicURL\": \"http://192.168.122.250:8989/v2\"}], \"type\": \"workflowv2\", \"name\": \"mistral\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9696/\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9696/\", \"publicURL\": \"http://192.168.122.250:9696/\"}], \"type\": \"network\", \"name\": \"neutron\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8776/v3/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8776/v3/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8776/v3/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"volumev3\", \"name\": \"cinderv3\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8082\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8082\", \"publicURL\": \"http://192.168.122.250:8082\"}], \"type\": \"application-catalog\", \"name\": \"murano\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8779/v1.0/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8779/v1.0/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8779/v1.0/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"database\", \"name\": \"trove\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8000/v1\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8000/v1\", \"publicURL\": \"http://192.168.122.250:8000/v1\"}], \"type\": \"cloudformation\", \"name\": \"heat-cfn\"}]",
        "project_id": "bde60e557de840a8a837733aaa96e42e",
        "user_name": "demo"
    },
    "mea_id": "f467e215-43a3-4083-8bbb-ce49d9c70443",
    "__env": {},
    "__execution": {
        "input": {
            "mea_id": "f467e215-43a3-4083-8bbb-ce49d9c70443"
        },
        "params": {},
        "id": "677c7bab-18ee-4a34-b1e6-a305e98ba887",
        "spec": {
            "tasks": {
                "delete_mea": {
                    "action": "apmec.delete_mea mea=<% $.mea_id %>",
                    "version": "2.0",
                    "type": "direct",
                    "description": "Request to delete a MEA.",
                    "name": "delete_mea"
                }
            },
            "description": "Delete a MEA.\n",
            "version": "2.0",
            "input": [
                "mea_id"
            ],
            "type": "direct",
            "name": "std.delete_mea"
        }
      }
  }


MEAD resource deletion with std.delete_mead workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Update the mead_id from the output of above execution in delete_mead.json

Create new execution for MEA deletion.

::

  $ mistral execution-create std.delete_mead delete_mead.json

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 1e0340c0-bee8-4ca4-8150-ac6e5eb58c99 |
  | Workflow ID       | f15b7402-ce31-4369-98d4-818125191564 |
  | Workflow name     | std.delete_mead                      |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | RUNNING                              |
  | State info        | None                                 |
  | Created at        | 2016-08-14 20:57:06.500941           |
  | Updated at        | 2016-08-14 20:57:06.505780           |
  +-------------------+--------------------------------------+

Gather execution details based on execution id.

::

  $ mistral execution-get 1e0340c0-bee8-4ca4-8150-ac6e5eb58c99

  +-------------------+--------------------------------------+
  | Field             | Value                                |
  +-------------------+--------------------------------------+
  | ID                | 1e0340c0-bee8-4ca4-8150-ac6e5eb58c99 |
  | Workflow ID       | f15b7402-ce31-4369-98d4-818125191564 |
  | Workflow name     | std.delete_mead                      |
  | Description       |                                      |
  | Task Execution ID | <none>                               |
  | State             | SUCCESS                              |
  | State info        | None                                 |
  | Created at        | 2016-08-14 20:57:06                  |
  | Updated at        | 2016-08-14 20:57:07                  |
  +-------------------+--------------------------------------+



Gather execution output data from execution id.

::

  $ mistral execution-get-output 1e0340c0-bee8-4ca4-8150-ac6e5eb58c99

  Response:

  {
    "openstack": {
        "project_name": "demo",
        "user_id": "f39a28fa574848dfa950b50329c1309b",
        "roles": [
            "anotherrole",
            "Member"
        ],
        "auth_uri": "http://192.168.122.250:5000/v3",
        "auth_cacert": null,
        "auth_token": "176c9b5ebd9d40fb9fb0a8db921609eb",
        "is_trust_scoped": false,
        "service_catalog": "[{\"endpoints\": [{\"adminURL\": \"http://192.168.122.250/identity_v2_admin\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250/identity\", \"publicURL\": \"http://192.168.122.250/identity\"}], \"type\": \"identity\", \"name\": \"keystone\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9292\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9292\", \"publicURL\": \"http://192.168.122.250:9292\"}], \"type\": \"image\", \"name\": \"glance\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8774/v2.1\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8774/v2.1\", \"publicURL\": \"http://192.168.122.250:8774/v2.1\"}], \"type\": \"compute\", \"name\": \"nova\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8776/v2/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8776/v2/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8776/v2/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"volumev2\", \"name\": \"cinderv2\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8776/v1/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8776/v1/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8776/v1/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"volume\", \"name\": \"cinder\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9494\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9494\", \"publicURL\": \"http://192.168.122.250:9494\"}], \"type\": \"artifact\", \"name\": \"glare\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8004/v1/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8004/v1/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8004/v1/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"orchestration\", \"name\": \"heat\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8774/v2/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8774/v2/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8774/v2/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"compute_legacy\", \"name\": \"nova_legacy\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9896/\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9896/\", \"publicURL\": \"http://192.168.122.250:9896/\"}], \"type\": \"mec-orchestration\", \"name\": \"apmec\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8989/v2\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8989/v2\", \"publicURL\": \"http://192.168.122.250:8989/v2\"}], \"type\": \"workflowv2\", \"name\": \"mistral\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:9696/\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:9696/\", \"publicURL\": \"http://192.168.122.250:9696/\"}], \"type\": \"network\", \"name\": \"neutron\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8776/v3/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8776/v3/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8776/v3/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"volumev3\", \"name\": \"cinderv3\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8082\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8082\", \"publicURL\": \"http://192.168.122.250:8082\"}], \"type\": \"application-catalog\", \"name\": \"murano\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8779/v1.0/bde60e557de840a8a837733aaa96e42e\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8779/v1.0/bde60e557de840a8a837733aaa96e42e\", \"publicURL\": \"http://192.168.122.250:8779/v1.0/bde60e557de840a8a837733aaa96e42e\"}], \"type\": \"database\", \"name\": \"trove\"}, {\"endpoints\": [{\"adminURL\": \"http://192.168.122.250:8000/v1\", \"region\": \"RegionOne\", \"internalURL\": \"http://192.168.122.250:8000/v1\", \"publicURL\": \"http://192.168.122.250:8000/v1\"}], \"type\": \"cloudformation\", \"name\": \"heat-cfn\"}]",
        "project_id": "bde60e557de840a8a837733aaa96e42e",
        "user_name": "demo"
      },
      "mead_id": "fb164b77-5e24-402d-b5f4-c6596352cabe",
      "__env": {},
      "__execution": {
        "input": {
            "mead_id": "fb164b77-5e24-402d-b5f4-c6596352cabe"
        },
        "params": {},
        "id": "1e0340c0-bee8-4ca4-8150-ac6e5eb58c99",
        "spec": {
            "tasks": {
                "delete_mead": {
                    "action": "apmec.delete_mead mead=<% $.mead_id %>",
                    "version": "2.0",
                    "type": "direct",
                    "description": "Request to delete a MEAD.",
                    "name": "delete_mead"
                }
            },
            "description": "Delete a MEAD.\n",
            "version": "2.0",
            "input": [
                "mead_id"
            ],
            "type": "direct",
            "name": "std.delete_mead"
          }
      }
  }
