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

.. _ref-mesd:

==========================================================
Orchestrating MEAs using Network Services Descriptor (MESD)
==========================================================

To enable dynamic composition of network services, MEC introduces Network
Service Descriptors (MESDs) that specify the network service to be created.
This usage guide describes lifecycle of Network service descriptors and
services.

MESD in Ocata can be used for creating multiple (related) MEAs in one shot
using a single TOSCA template. This is a first (big) step into MESD, few
follow-on enhancements like:
1) Creating VLs / neutron networks using MESD (to support inter-MEA private VL)
2) NFYD support in MESD.

Creating the MESD
~~~~~~~~~~~~~~~~

Once OpenStack along with Apmec has been successfully installed,
deploy a sample MEAD templates using mea1.yaml and mea2.yaml as mentioned in
reference section.

::

  apmec mead-create --mead-file mead1.yaml MEAD1

  apmec mead-create --mead-file mead2.yaml MEAD2

The following code represents sample MESD which instantiates the above MEAs

::

    tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0
    imports:
      - MEAD1
      - MEAD2
    topology_template:
      node_templates:
        MEA1:
          type: tosca.nodes.mec.MEA1
          requirements:
            - virtualLink1: VL1
            - virtualLink2: VL2
        MEA2:
          type: tosca.nodes.mec.MEA2
        VL1:
          type: tosca.nodes.mec.VL
          properties:
          network_name: net0
          vendor: apmec
        VL2:
          type: tosca.nodes.mec.VL
          properties:
              network_name: net_mgmt
              vendor: apmec

In above MESD template VL1 and VL2 are substituting the virtuallinks of MEA1.
To onboard the above  MESD:

::

   apmec mesd-create --mesd-file <mesd-file> <mesd-name>

Creating the MES
~~~~~~~~~~~~~~~~

To create a MES, you must have onboarded corresponding MESD and
MEADS(which MES is substituting)

Apmec provides the following CLI to create MES:

::

    apmec mes-create --mesd-id <mesd-id> <mes-name>

Or you can create directly a MES without creating onboarded MESD before by
following CLI command:

::

    apmec mes-create --mesd-template <mesd-file> <mes-name>

Reference
~~~~~~~~~

MEA1 sample template for mesd named mead1.yaml:

::

 tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0
 description: Demo example
 node_types:
   tosca.nodes.mec.MEA1:
     requirements:
       - virtualLink1:
           type: tosca.nodes.mec.VL
           required: true
       - virtualLink2:
           type: tosca.nodes.mec.VL
           required: true
     capabilities:
       forwarder1:
         type: tosca.capabilities.mec.Forwarder
       forwarder2:
         type: tosca.capabilities.mec.Forwarder

 topology_template:
   substitution_mappings:
     node_type: tosca.nodes.mec.MEA1
     requirements:
       virtualLink1: [CP11, virtualLink]
       virtualLink2: [CP14, virtualLink]
     capabilities:
       forwarder1: [CP11, forwarder]
       forwarder2: [CP14, forwarder]
   node_templates:
     VDU1:
       type: tosca.nodes.mec.VDU.Apmec
       properties:
         image: cirros-0.3.5-x86_64-disk
         flavor: m1.tiny
         availability_zone: nova
         mgmt_driver: noop
         config: |
           param0: key1
           param1: key2
     CP11:
       type: tosca.nodes.mec.CP.Apmec
       properties:
         management: true
         anti_spoofing_protection: false
       requirements:
         - virtualBinding:
             node: VDU1

     VDU2:
       type: tosca.nodes.mec.VDU.Apmec
       properties:
         image: cirros-0.3.5-x86_64-disk
         flavor: m1.medium
         availability_zone: nova
         mgmt_driver: noop
         config: |
           param0: key1
           param1: key2
     CP13:
       type: tosca.nodes.mec.CP.Apmec
       properties:
         management: true
         anti_spoofing_protection: false
       requirements:
         - virtualLink:
             node: VL1
         - virtualBinding:
             node: VDU2
     CP14:
       type: tosca.nodes.mec.CP.Apmec
       properties:
         management: true
         anti_spoofing_protection: false
       requirements:
         - virtualBinding:
             node: VDU2
     VL1:
       type: tosca.nodes.mec.VL
       properties:
         network_name: net_mgmt
         vendor: Apmec
     VL2:
       type: tosca.nodes.mec.VL
       properties:
         network_name: net0
         vendor: Apmec

MEA2 sample template for mesd named mead2.yaml:

::

  tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0
  description: Demo example

  node_types:
    tosca.nodes.mec.MEA2:
      capabilities:
        forwarder1:
          type: tosca.capabilities.mec.Forwarder
  topology_template:
    substitution_mappings:
      node_type: tosca.nodes.mec.MEA2
      capabilities:
        forwarder1: [CP21, forwarder]
    node_templates:
      VDU1:
        type: tosca.nodes.mec.VDU.Apmec
        properties:
          image: cirros-0.3.5-x86_64-disk
          flavor: m1.tiny
          availability_zone: nova
          mgmt_driver: noop
          config: |
            param0: key1
            param1: key2
      CP21:
        type: tosca.nodes.mec.CP.Apmec
        properties:
          management: true
          anti_spoofing_protection: false
        requirements:
          - virtualLink:
              node: VL1
          - virtualBinding:
              node: VDU1
      VDU2:
        type: tosca.nodes.mec.VDU.Apmec
        properties:
          image: cirros-0.3.5-x86_64-disk
          flavor: m1.medium
          availability_zone: nova
          mgmt_driver: noop
      CP22:
        type: tosca.nodes.mec.CP.Apmec
        properties:
          management: true
          anti_spoofing_protection: false
        requirements:
          - virtualLink:
              node: VL2
          - virtualBinding:
              node: VDU2
      VL1:
        type: tosca.nodes.mec.VL
        properties:
          network_name: net_mgmt
          vendor: Apmec
      VL2:
        type: tosca.nodes.mec.VL
        properties:
          network_name: net0
          vendor: Apmec


