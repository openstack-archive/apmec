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

===============
Getting Started
===============

Once apmec is installed successfully, follow the steps given below to get
started with apmec and validate the installation.


Registering default OpenStack VIM
=================================
1.) Get one account on the OpenStack VIM.

In Apmec MANO system, the MEA can be onboarded to one target OpenStack, which
is also called VIM. Get one account on this OpenStack. For example, the below
is the account information collected in file vim-config.yaml::

    auth_url: 'http://10.1.0.5:5000'
    username: 'mec_user'
    password: 'mySecretPW'
    project_name: 'mec'
    project_domain_name: 'Default'
    user_domain_name: 'Default'


2.) Register the VIM that will be used as a default VIM for MEA deployments.
This will be required when the optional argument --vim-id is not provided by
the user during mea-create.

.. code-block:: console

   apmec vim-register --is-default --config-file vim-config.yaml \
          --description 'my first vim' hellovim
..



Onboarding sample MEA
=====================

1). Create a sample-mead.yaml file with the following content:

.. code-block:: ini

   tosca_definitions_version: tosca_simple_profile_for_mec_1_0_0

   description: Demo example

   metadata:
     template_name: sample-tosca-mead

   topology_template:
     node_templates:
       VDU1:
         type: tosca.nodes.mec.VDU.Apmec
         capabilities:
           mec_compute:
             properties:
               num_cpus: 1
               mem_size: 512 MB
               disk_size: 1 GB
         properties:
           image: cirros-0.3.5-x86_64-disk
           availability_zone: nova
           mgmt_driver: noop
           config: |
             param0: key1
             param1: key2

       CP1:
         type: tosca.nodes.mec.CP.Apmec
         properties:
           management: true
           order: 0
           anti_spoofing_protection: false
         requirements:
           - virtualLink:
               node: VL1
           - virtualBinding:
               node: VDU1

       VL1:
         type: tosca.nodes.mec.VL
         properties:
           network_name: net_mgmt
           vendor: Apmec

..

.. note::

   You can find more sample tosca templates at
   https://github.com/openstack/apmec/tree/master/samples/tosca-templates/mead.


2). Create a sample mead.

.. code-block:: console

   apmec mead-create --mead-file sample-mead.yaml samplemead
..

3). Create a MEA.

.. code-block:: console

   apmec mea-create --mead-name samplemead samplemea
..

5). Check the status.

.. code-block:: console

   apmec vim-list
   apmec mead-list
   apmec mea-list
   apmec mea-show samplemea
..
