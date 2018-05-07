MEAD Template Parameterization
==============================

Overview
--------

Parameterization allows for the ability to use a single MEAD to be deployed
multiple times with different values for the VDU parameters provided at
deploy time. In contrast, a non-parameterized MEAD has static values
for the parameters that might limit the number of concurrent MEAs that can be
deployed using a single MEAD. For example, deploying an instance of a
non-parameterized template that has fixed IP addresses specified for network
interface a second time without deleting the first instance of MEA would lead
to an error.

Non-parameterized MEAD template
-------------------------------

Find below an example of a non-parameterized MEAD where the text italicized
are the VDU parameters and text in bold are the values for those VDU
parameters that get applied to the VDU when this template is deployed.
The next section will illustrate how the below non-parameterized template
can be parameterized and re-used for deploying multiple MEAs.

Here is the sample template:

.. code-block:: yaml

   tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0

   description: MEA TOSCA template with input parameters

   metadata:
     template_name: sample-tosca-mead

   topology_template:

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

       CP1:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           management: True
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL1
           - virtualBinding:
               node: VDU1

       CP2:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL2
           - virtualBinding:
               node: VDU1

       CP3:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL3
           - virtualBinding:
               node: VDU1

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

       VL3:
         type: tosca.nodes.mec.VL
         properties:
           network_name: net1
           vendor: Apmec


Parameterized MEAD template
---------------------------
This section will walk through parameterizing the template in above section
for re-use and allow for deploying multiple MEAs with the same template.
(Note: All the parameters italicized in the above template could be
parameterized to accept values at deploy time).
For the current illustration purpose, we will assume that an end user would
want to be able to supply different values for the parameters
**image_name**, **flavor**, **network**, **management**, **pkt_in_network**,
**pkt_out_network**, **vendor**, during each deploy of the MEA.

The next step is to substitute the identified parameter values that will be
provided at deploy time with { get_input: <param_name>}. For example, the
instance_type: **cirros-0.3.5-x86_64-disk** would now be replaced as:
**image: {get_input: image_name}**. The **get_input** is a reserved
keyword in the template that indicates value will be supplied at deploy time
for the parameter instance_type. The **image_name** is the variable that will
hold the value for the parameter **image** in a parameters value file
that will be supplied at MEA deploy time.

The template in above section will look like below when parameterized for
**image_name**, **flavor**, **network**, **management** and remaining
parameters.

Here is the sample template:

.. code-block:: yaml

   tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0

   description: MEA TOSCA template with input parameters

   metadata:
     template_name: sample-tosca-mead

   topology_template:
     inputs:
       image_name:
         type: string
         description: Image Name

       flavor:
         type: string
         description: Flavor Information

       zone:
         type: string
         description: Zone Information

       network:
         type: string
         description: management network

       management:
         type: string
         description: management network

       pkt_in_network:
         type: string
         description: In network

       pkt_out_network:
         type: string
         description: Out network

       vendor:
         type: string
         description: Vendor information

     node_templates:
       VDU1:
         type: tosca.nodes.mec.VDU.Apmec
         properties:
           image: { get_input: image_name}
           flavor: {get_input: flavor}
           availability_zone: { get_input: zone }
           mgmt_driver: noop
           config: |
             param0: key1
             param1: key2

       CP1:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           management: { get_input: management }
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL1
           - virtualBinding:
               node: VDU1

       CP2:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL2
           - virtualBinding:
               node: VDU1

       CP3:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL3
           - virtualBinding:
               node: VDU1

       VL1:
         type: tosca.nodes.mec.VL
         properties:
           network_name: { get_input: network }
           vendor: {get_input: vendor}

       VL2:
         type: tosca.nodes.mec.VL
         properties:
           network_name: { get_input: pkt_in_network }
           vendor: {get_input: vendor}

       VL3:
         type: tosca.nodes.mec.VL
         properties:
           network_name: { get_input: pkt_out_network }
           vendor: {get_input: vendor}


Parameter values file at MEA deploy
-----------------------------------
The below illustrates the parameters value file to be supplied containing the
values to be substituted for the above parameterized template above during
MEA deploy.

.. code-block:: yaml

    image_name: cirros-0.3.5-x86_64-disk
    flavor: m1.tiny
    zone: nova
    network: net_mgmt
    management: True
    pkt_in_network: net0
    pkt_out_network: net1
    vendor: Apmec


.. note::

   IP address values for network interfaces should be in the below format
   in the parameters values file:

   param_name_value:
     \- xxx.xxx.xxx.xxx


Key Summary
-----------
#. Parameterize your MEAD if you want to re-use for multiple MEA deployments.
#. Identify parameters that would need to be provided values at deploy time
   and substitute value in MEAD template with {get_input: <param_value_name>},
   where 'param_value_name' is the name of the variable that holds the value
   in the parameters value file.
#. Supply a parameters value file in yaml format each time during MEA
   deployment with different values for the parameters.
#. An example of a mea-create python-apmecclient command specifying a
   parameterized template and parameter values file would like below:

   .. code-block:: console

      apmec mea-create --mead-name <mead_name> --param-file <param_yaml_file> <mea_name>

#. Specifying a parameter values file during MEA creation is also supported in
   Horizon UI.
#. Sample MEAD parameterized templates and parameter values files can be found
   at https://github.com/openstack/apmec/tree/master/samples/tosca-templates/mead.
