..
      Copyright 2010-2015 United States Government as represented by the
      Administrator of the National Aeronautics and Space Administration.
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

Setting Up a Development Environment
====================================

This page describes how to setup a working Python development
environment that can be used in developing Apmec on Ubuntu, Fedora or
Mac OS X. These instructions assume you're already familiar with
Git and Gerrit, which is a code repository mirror and code review toolset
, however if you aren't please see `this Git tutorial`_ for an introduction
to using Git and `this guide`_ for a tutorial on using Gerrit and Git for
code contribution to Openstack projects.

.. _this Git tutorial: http://git-scm.com/book/en/Getting-Started
.. _this guide: https://docs.openstack.org/infra/manual/developers.html#development-workflow

If you want to be able to run Apmec in a full OpenStack environment,
you can use the excellent `DevStack`_ project to do so. There is a wiki page
that describes `setting up Apmec using DevStack`_.

.. _DevStack: https://git.openstack.org/cgit/openstack-dev/devstack
.. _setting up Apmec using Devstack: https://wiki.openstack.org/wiki/Apmec/Installation

Getting the code
----------------

Grab the code::

    git clone https://git.openstack.org/openstack/apmec.git
    cd apmec


.. include:: ../../../TESTING.rst
