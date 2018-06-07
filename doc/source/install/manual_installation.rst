..
      Copyright 2015-2016 Brocade Communications Systems Inc
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


===================
Manual Installation
===================

This document describes how to install and run Apmec manually.

Pre-requisites
==============

1). Ensure that OpenStack components Keystone, Mistral, Barbican and
Horizon are installed. Refer https://docs.openstack.org/latest/projects.html
for installation of these OpenStack projects on different Operating Systems.

2). one admin-openrc.sh file is generated. one sample admin-openrc.sh file
is like the below:

.. code-block:: ini

    export OS_PROJECT_DOMAIN_NAME=Default
    export OS_USER_DOMAIN_NAME=Default
    export OS_PROJECT_NAME=admin
    export OS_TENANT_NAME=admin
    export OS_USERNAME=admin
    export OS_PASSWORD=KTskN5eUMTpeHLKorRcZBBbH0AM96wdvgQhwENxY
    export OS_AUTH_URL=http://localhost:5000/v3
    export OS_INTERFACE=internal
    export OS_IDENTITY_API_VERSION=3
    export OS_REGION_NAME=RegionOne


Installing Apmec server
========================

.. note::

   The paths we are using for configuration files in these steps are with reference to
   Ubuntu Operating System. The paths may vary for other Operating Systems.

   The branch_name which is used in commands, specify the branch_name as
   "stable/<branch>" for any stable branch installation.
   For eg: stable/ocata, stable/newton. If unspecified the default will be
   "master" branch.


1). Create MySQL database and user.

.. code-block:: console

   mysql -uroot -p
   CREATE DATABASE apmec;
   GRANT ALL PRIVILEGES ON apmec.* TO 'apmec'@'localhost' \
       IDENTIFIED BY '<APMECDB_PASSWORD>';
   GRANT ALL PRIVILEGES ON apmec.* TO 'apmec'@'%' \
       IDENTIFIED BY '<APMECDB_PASSWORD>';
   exit;
..

.. note::

   Replace ``APMECDB_PASSWORD`` with your password.

2). Create users, roles and endpoints:

a). Source the admin credentials to gain access to admin-only CLI commands:

.. code-block:: console

   . admin-openrc.sh
..

b). Create apmec user with admin privileges.

.. note::

   Project_name can be "service" or "services" depending on your
   OpenStack distribution.
..

.. code-block:: console

   openstack user create --domain default --password <PASSWORD> apmec
   openstack role add --project service --user apmec admin
..

c). Create apmec service.

.. code-block:: console

   openstack service create --name apmec \
       --description "Apmec Project" mec-orchestration
..

d). Provide an endpoint to apmec service.

If you are using keystone v3 then,

.. code-block:: console

   openstack endpoint create --region RegionOne mec-orchestration \
              public http://<APMEC_NODE_IP>:9896/
   openstack endpoint create --region RegionOne mec-orchestration \
              internal http://<APMEC_NODE_IP>:9896/
   openstack endpoint create --region RegionOne mec-orchestration \
              admin http://<APMEC_NODE_IP>:9896/
..

If you are using keystone v2 then,

.. code-block:: console

   openstack endpoint create --region RegionOne \
        --publicurl 'http://<APMEC_NODE_IP>:9896/' \
        --adminurl 'http://<APMEC_NODE_IP>:9896/' \
        --internalurl 'http://<APMEC_NODE_IP>:9896/' <SERVICE-ID>
..

3). Clone apmec repository.

.. code-block:: console

   cd ~/
   git clone https://github.com/openstack/apmec -b <branch_name>
..

4). Install all requirements.

.. code-block:: console

   cd apmec
   sudo pip install -r requirements.txt
..


5). Install apmec.

.. code-block:: console

   sudo python setup.py install
..

..

6). Create 'apmec' directory in '/var/log'.

.. code-block:: console

   sudo mkdir /var/log/apmec

..

7). Generate the apmec.conf.sample using tools/generate_config_file_sample.sh
    or 'tox -e config-gen' command. Rename the "apmec.conf.sample" file at
    "etc/apmec/" to apmec.conf. Then edit it to ensure the below entries:

.. note::

   Ignore any warnings generated while using the
   "generate_config_file_sample.sh".

..

.. note::

   project_name can be "service" or "services" depending on your
   OpenStack distribution in the keystone_authtoken section.
..

.. code-block:: ini

   [DEFAULT]
   auth_strategy = keystone
   policy_file = /usr/local/etc/apmec/policy.json
   debug = True
   use_syslog = False
   bind_host = <APMEC_NODE_IP>
   bind_port = 9896
   service_plugins = meo,mem

   state_path = /var/lib/apmec
   ...

   [meo]
   vim_drivers = openstack

   [keystone_authtoken]
   memcached_servers = 11211
   region_name = RegionOne
   auth_type = password
   project_domain_name = <DOMAIN_NAME>
   user_domain_name = <DOMAIN_NAME>
   username = <APMEC_USER_NAME>
   project_name = service
   password = <APMEC_SERVICE_USER_PASSWORD>
   auth_url = http://<KEYSTONE_IP>:5000
   auth_uri = http://<KEYSTONE_IP>:5000
   ...

   [agent]
   root_helper = sudo /usr/local/bin/apmec-rootwrap /usr/local/etc/apmec/rootwrap.conf
   ...

   [database]
   connection = mysql://apmec:<APMECDB_PASSWORD>@<MYSQL_IP>:3306/apmec?charset=utf8
   ...

   [apmec]
   monitor_driver = ping,http_ping

..

8). Copy the apmec.conf file to "/usr/local/etc/apmec/" directory

.. code-block:: console

   sudo su
   cp etc/apmec/apmec.conf /usr/local/etc/apmec/

..

9). Populate Apmec database:

.. code-block:: console

   /usr/local/bin/apmec-db-manage --config-file /usr/local/etc/apmec/apmec.conf upgrade head

..


Install Apmec client
=====================

1). Clone apmec-client repository.

.. code-block:: console

   cd ~/
   git clone https://github.com/openstack/python-apmecclient -b <branch_name>
..

2). Install apmec-client.

.. code-block:: console

   cd python-apmecclient
   sudo python setup.py install
..

Install Apmec horizon
======================


1). Clone apmec-horizon repository.

.. code-block:: console

   cd ~/
   git clone https://github.com/openstack/apmec-horizon -b <branch_name>
..

2). Install horizon module.

.. code-block:: console

   cd apmec-horizon
   sudo python setup.py install
..

3). Enable apmec horizon in dashboard.

.. code-block:: console

   sudo cp apmec_horizon/enabled/* \
       /usr/share/openstack-dashboard/openstack_dashboard/enabled/
..

4). Restart Apache server.

.. code-block:: console

   sudo service apache2 restart
..

Starting Apmec server
======================

1).Open a new console and launch apmec-server. A separate terminal is
required because the console will be locked by a running process.

.. code-block:: console

   sudo python /usr/local/bin/apmec-server \
       --config-file /usr/local/etc/apmec/apmec.conf \
       --log-file /var/log/apmec/apmec.log
..
