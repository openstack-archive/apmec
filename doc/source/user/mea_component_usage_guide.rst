========================
MEA Component in Apmec
========================

This section will cover how to deploy `mea component` in Apmec with the
examples of how to write MEA descriptors.


Sample TOSCA with meac
=======================

The following example shows meac resource using TOSCA template.
The target (VDU1) of the 'firewall_meac' in this example need to be
described firstly like other TOSCA templates in Apmec.

.. code-block:: yaml

     topology_template:
       node_templates:
         firewall_meac:
           type: tosca.nodes.mec.MEAC.Apmec
           requirements:
             - host: VDU1
           interfaces:
             Standard:
               create: install_meac.sh

Every meac node must be of type 'tosca.nodes.mec.MEAC.Apmec'. It takes
two parameters:

1) requirements: This node will accept list of hosts on which MEAC has to be
   installed.
2) interfaces: This node will accept the absolute path of shell script to be run
   on the VDUs. This shell script should reside in the machine where apmec
   server is running.


How to setup environment
~~~~~~~~~~~~~~~~~~~~~~~~~
To make use of MEAC in Apmec, we have to upload the image to the glance in
which heat-config and heat-config agents are installed. The installation steps
can be referred `here <https://github.com/openstack/heat-templates/blob/master/
hot/software-config/elements/README.rst>`_. The tool
'tools/meac/build_image.sh' can be used to generate such a kind of image.

Currently MEAC feature works by using `heat software config <https://docs.openstack.org/heat/latest/
template_guide/software_deployment.html#software-config-resources>`_  which
makes use of heat API.

So the glance images which has heat-config agents installed are only to be
passed to VDU.

Known Limitations
~~~~~~~~~~~~~~~~~
1) Only one MEAC is supported for one VDU. Multiple MEAC per VDU will
   be introduced in future.
2) The shell script for meac has to be placed in the machine where apmec
   server is running.
