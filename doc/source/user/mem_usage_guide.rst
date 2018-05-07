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

======================
MEA Manager User Guide
======================

Apmec MEA Manager (MEM) component manages the life-cycle of a Virtual Network
Function (MEA). MEM takes care of deployment, monitoring, scaling and removal
of MEAs on a Virtual Infrastructure Manager (VIM).


Onboarding MEA
==============

TOSCA MEAD templates can be onboarded to Apmec MEAD Catalog using following
command:

.. code-block:: console

   apmec mead-create --mead-file <yaml file path> <MEAD-NAME>

.. note::

   Users can find various sample TOSCA templates at https://github.com/openstack/apmec/tree/master/samples/tosca-templates/mead

Deploying MEA
=============

There are two ways to create a MEA in Apmec.

#. Using Apmec Catalog
#. Direct MEA Instantiation

Using Apmec Catalog
--------------------

In this method, a TOSCA MEAD template is first onboarded into Apmec MEAD
catalog. This MEAD is then used to create MEA. This is most common way of
creating MEAs in Apmec.

   i). Onboard a TOSCA MEAD template.

.. code-block:: console

   apmec mead-create --mead-file <yaml file path> <MEAD-NAME>
..

  ii). Create a MEA.

.. code-block:: console

   apmec mea-create --mead-name <MEAD-FILE-NAME> <MEA-NAME>


Example
~~~~~~~

.. code-block:: console

    apmec mead-create --mead-file sample-mead-hello-world.yaml hello-world-mead
    apmec mea-create --mead-name hello-world-mead hw-mea

Direct MEA Instantiation
------------------------

In this method, MEA is created directly from the TOSCA template without
onboarding the template into Apmec MEAD Catalog.

.. code-block:: console

   apmec mea-create --mead-template <MEAD-FILE-NAME> <MEA-NAME>

This method is recommended when MEM Catalog is maintained outside Apmec and
Apmec is primarily used as a MEM workflow engine.

Example
~~~~~~~

.. code-block:: console

    apmec mea-create --mead-template sample-mead-hello-world.yaml hw-mea

.. note ::

    mead-list command will show only the onboarded MEADs. To list the MEADs
    created internally for direct MEA instantiation, use
    '--template-source inline' flag. To list both onboarded and inline MEADs,
    use '--template-source all' flag. The default flag for mead-list command
    is '--template-source onboarded'.

    .. code-block:: console

      apmec mead-list --template-source inline
      apmec mead-list --template-source all

Finding MEM Status
===================

Status of various MEM resources can be checked by following commands.

.. code-block:: console

   apmec vim-list
   apmec mead-list
   apmec mea-list
   apmec mea-show <MEA_ID>
   apmec mead-show <MEAD_ID>

..

Deleting MEA and MEAD
=====================

MEAs and MEADs can be deleted as shown below.

.. code-block:: console

   apmec mea-delete <MEA_ID/NAME>
   apmec mead-delete <MEAD_ID/NAME>
..
