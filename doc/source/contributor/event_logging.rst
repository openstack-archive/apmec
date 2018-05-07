..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

Apmec Resource Events Usage Guide
==================================

Overview
--------

OpenStack Apmec supports capturing resource event information when the
apmec resources undergo  create, update, delete, scale and monitor
operations. This information becomes useful to an admin for audit purposes.

Apmec Resources supporting Events
----------------------------------
As of Newton release, events information is captured for below:

- MEA

- MEAD

- VIM

Apmec supported event types
----------------------------
Below are the event types that are currently supported:

- CREATE

- DELETE

- MONITOR

- SCALE

- UPDATE

The above can be used as filters when listing events using apmec client.

Accessing Events
----------------

Apmec supports display of events to an end user via

- Horizon UI - a separate events tab per resource displays associated events.

- Apmec Client - supports below commands:
    - event-show: Show detailed info for a given event ID.
    - events-list: Lists all events for all resources.
    - vim-events-list: List events that belong to a given VIM.
    - mea-events-list: List events that belong to a given MEA.
    - mead-events-list: List events that belong to a given MEAD.

NOTE: For more details on the syntax of these CLIs, refer to
`Apmec CLI reference guide <http://docs.openstack.org/cli-reference/apmec.html>`_

Apmec Client command usage examples to access resource lifecycle events
------------------------------------------------------------------------

1. The following command displays all the state transitions that occurred on
a long running MEA.  The sample output illustrates a MEA that has
successfully gone through a scale out operation. Note, the <resource_id> here
is MEA's uuid.

.. code-block:: console

  apmec mea-events-list --resource_id <resource_id>

  +----+---------------+-------------------+-------------------+------------+-------------------+---------------------+
  | id | resource_type | resource_id       | resource_state    | event_type | timestamp         | event_details       |
  +----+---------------+-------------------+-------------------+------------+-------------------+---------------------+
  | 13 | mea           | 9dd7b2f1-e91e-418 | PENDING_CREATE    | CREATE     | 2016-09-21        | MEA UUID assigned.  |
  |    |               | 3-bcbe-           |                   |            | 20:12:37          |                     |
  |    |               | 34b80bdb18fb      |                   |            |                   |                     |
  | 14 | mea           | 9dd7b2f1-e91e-418 | PENDING_CREATE    | CREATE     | 2016-09-21        | Infra Instance ID   |
  |    |               | 3-bcbe-           |                   |            | 20:13:09          | created: 3bd369e4-9 |
  |    |               | 34b80bdb18fb      |                   |            |                   | ee3-4e58-86e3-8acbb |
  |    |               |                   |                   |            |                   | dccedb5 and Mgmt    |
  |    |               |                   |                   |            |                   | URL set: {"VDU1":   |
  |    |               |                   |                   |            |                   | ["10.0.0.9",        |
  |    |               |                   |                   |            |                   | "10.0.0.2"],        |
  |    |               |                   |                   |            |                   | "VDU2":             |
  |    |               |                   |                   |            |                   | ["10.0.0.4",        |
  |    |               |                   |                   |            |                   | "10.0.0.5"]}        |
  | 15 | mea           | 9dd7b2f1-e91e-418 | ACTIVE            | CREATE     | 2016-09-21        | MEA status updated  |
  |    |               | 3-bcbe-           |                   |            | 20:13:09          |                     |
  |    |               | 34b80bdb18fb      |                   |            |                   |                     |
  | 16 | mea           | 9dd7b2f1-e91e-418 | PENDING_SCALE_OUT | SCALE      | 2016-09-21        |                     |
  |    |               | 3-bcbe-           |                   |            | 20:23:58          |                     |
  |    |               | 34b80bdb18fb      |                   |            |                   |                     |
  | 17 | mea           | 9dd7b2f1-e91e-418 | ACTIVE            | SCALE      | 2016-09-21        |                     |
  |    |               | 3-bcbe-           |                   |            | 20:24:45          |                     |
  |    |               | 34b80bdb18fb      |                   |            |                   |                     |
  +----+---------------+-------------------+-------------------+------------+-------------------+---------------------+

2. The following command displays any reachability issues related to a VIM
site. The sample output illustrates a VIM that is reachable. Note, the
<resource_id> here is a VIM uuid.

.. code-block:: console

  apmec vim-events-list --resource_id <resource_id>

  +----+---------------+---------------------+----------------+------------+---------------------+---------------+
  | id | resource_type | resource_id         | resource_state | event_type | timestamp           | event_details |
  +----+---------------+---------------------+----------------+------------+---------------------+---------------+
  |  1 | vim           | d8c11a53-876c-454a- | PENDING        | CREATE     | 2016-09-20 23:07:42 |               |
  |    |               | bad1-cb13ad057595   |                |            |                     |               |
  |  2 | vim           | d8c11a53-876c-454a- | REACHABLE      | MONITOR    | 2016-09-20 23:07:42 |               |
  |    |               | bad1-cb13ad057595   |                |            |                     |               |
  +----+---------------+---------------------+----------------+------------+---------------------+---------------+


Miscellaneous events command examples:
--------------------------------------

1. List all events for all resources from the beginning

.. code-block:: console

  apmec events-list

  +----+---------------+-----------------+----------------+------------+-----------------+-----------------+
  | id | resource_type | resource_id     | resource_state | event_type | timestamp       | event_details   |
  +----+---------------+-----------------+----------------+------------+-----------------+-----------------+
  |  1 | vim           | c89e5d9d-6d55-4 | PENDING        | CREATE     | 2016-09-10      |                 |
  |    |               | db1-bd67-30982f |                |            | 20:32:46        |                 |
  |    |               | 01133e          |                |            |                 |                 |
  |  2 | vim           | c89e5d9d-6d55-4 | REACHABLE      | MONITOR    | 2016-09-10      |                 |
  |    |               | db1-bd67-30982f |                |            | 20:32:46        |                 |
  |    |               | 01133e          |                |            |                 |                 |
  |  3 | mead          | afc0c662-5117-4 | Not Applicable | CREATE     | 2016-09-14      |                 |
  |    |               | 7a7-8088-02e9f8 |                |            | 05:17:30        |                 |
  |    |               | a3532b          |                |            |                 |                 |
  |  4 | mea           | 52adaae4-36b5   | PENDING_CREATE | CREATE     | 2016-09-14      | MEA UUID        |
  |    |               | -41cf-acb5-32ab |                |            | 17:49:24        | assigned.       |
  |    |               | 8c109265        |                |            |                 |                 |
  |  5 | mea           | 52adaae4-36b5   | PENDING_CREATE | CREATE     | 2016-09-14      | Infra Instance  |
  |    |               | -41cf-acb5-32ab |                |            | 17:49:51        | ID created:     |
  |    |               | 8c109265        |                |            |                 | 046dcb04-318d-4 |
  |    |               |                 |                |            |                 | ec9-8a23-19d9c1 |
  |    |               |                 |                |            |                 | f8c21d and Mgmt |
  |    |               |                 |                |            |                 | URL set:        |
  |    |               |                 |                |            |                 | {"VDU1": "192.1 |
  |    |               |                 |                |            |                 | 68.120.8"}      |
  |  6 | mea           | 52adaae4-36b5   | ACTIVE         | CREATE     | 2016-09-14      | MEA status      |
  |    |               | -41cf-acb5-32ab |                |            | 17:49:51        | updated         |
  |    |               | 8c109265        |                |            |                 |                 |
  +----+---------------+-----------------+----------------+------------+-----------------+-----------------+

2. List all events for all resources given a certain event type

.. code-block:: console

  apmec events-list --event_type CREATE

  +----+---------------+-----------------+----------------+------------+-----------------+-----------------+
  | id | resource_type | resource_id     | resource_state | event_type | timestamp       | event_details   |
  +----+---------------+-----------------+----------------+------------+-----------------+-----------------+
  |  1 | vim           | c89e5d9d-6d55-4 | PENDING        | CREATE     | 2016-09-10      |                 |
  |    |               | db1-bd67-30982f |                |            | 20:32:46        |                 |
  |    |               | 01133e          |                |            |                 |                 |
  |  3 | mead          | afc0c662-5117-4 | ACTIVE         | CREATE     | 2016-09-14      |                 |
  |    |               | 7a7-8088-02e9f8 |                |            | 05:17:30        |                 |
  |    |               | a3532b          |                |            |                 |                 |
  |  4 | mea           | 52adaae4-36b5   | PENDING_CREATE | CREATE     | 2016-09-14      | MEA UUID        |
  |    |               | -41cf-acb5-32ab |                |            | 17:49:24        | assigned.       |
  |    |               | 8c109265        |                |            |                 |                 |
  |  5 | mea           | 52adaae4-36b5   | PENDING_CREATE | CREATE     | 2016-09-14      | Infra Instance  |
  |    |               | -41cf-acb5-32ab |                |            | 17:49:51        | ID created:     |
  |    |               | 8c109265        |                |            |                 | 046dcb04-318d-4 |
  |    |               |                 |                |            |                 | ec9-8a23-19d9c1 |
  |    |               |                 |                |            |                 | f8c21d and Mgmt |
  |    |               |                 |                |            |                 | URL set:        |
  |    |               |                 |                |            |                 | {"VDU1": "192.1 |
  |    |               |                 |                |            |                 | 68.120.8"}      |
  |  6 | mea           | 52adaae4-36b5   | ACTIVE         | CREATE     | 2016-09-14      | MEA status      |
  |    |               | -41cf-acb5-32ab |                |            | 17:49:51        | updated         |
  |    |               | 8c109265        |                |            |                 |                 |
  +----+---------------+-----------------+----------------+------------+-----------------+-----------------+


3. List details for a specific event

.. code-block:: console

  apmec event-show 5

  +----------------+------------------------------------------------------------------------------------------+
  | Field          | Value                                                                                    |
  +----------------+------------------------------------------------------------------------------------------+
  | event_details  | Infra Instance ID created: 046dcb04-318d-4ec9-8a23-19d9c1f8c21d and Mgmt URL set:        |
  |                | {"VDU1": "192.168.120.8"}                                                                |
  | event_type     | CREATE                                                                                   |
  | id             | 5                                                                                        |
  | resource_id    | 52adaae4-36b5-41cf-acb5-32ab8c109265                                                     |
  | resource_state | PENDING_CREATE                                                                           |
  | resource_type  | mea                                                                                      |
  | timestamp      | 2016-09-14 17:49:51                                                                      |
  +----------------+------------------------------------------------------------------------------------------+


Note for Apmec developers
--------------------------

If as a developer, you are creating new resources and would like to capture
event information for resource operations such as create, update, delete,
scale and monitor, you would need to :

- Import the module apmec.db.common_services.common_services_db to use the
  create_event() method for logging events.

- Make edits in the file apmec/plugins/common/constants.py if you would need
  to create new event types.
