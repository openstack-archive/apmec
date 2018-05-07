Apmec Monitoring Framework
============================

This section will introduce apmec monitoring framework and describes the
various actions that a user can take when a specific event occurs.

* Introduction
* How to write a new monitor driver
* Events
* Actions
* How to write TOSCA template to monitor MEA entities

Introduction
-------------

Apmec monitoring framework provides the MEM operators and MEA vendors to
write a pluggable driver that monitors the various status conditions of the
MEA entities it deploys and manages.

How to write a new monitor driver
----------------------------------

A monitor driver for apmec is a python module which contains a class that
inherits from
"apmec.mem.monitor_drivers.abstract_driver.MEAMonitorAbstractDriver". If the
driver depends/imports more than one module, then create a new python package
under apmec/mem/monitor_drivers folder. After this we have to mention our
driver path in setup.cfg file in root directory.

For example:
::

  apmec.apmec.monitor_drivers =
      ping = apmec.mem.monitor_drivers.ping.ping:MEAMonitorPing

Following methods need to be overridden in the new driver:

``def get_type(self)``
    This method must return the type of driver. ex: ping

``def get_name(self)``
    This method must return the symbolic name of the mea monitor plugin.

``def get_description(self)``
    This method must return the description for the monitor driver.

``def monitor_get_config(self, plugin, context, mea)``
    This method must return dictionary of configuration data for the monitor
    driver.

``def monitor_url(self, plugin, context, mea)``
    This method must return the url of mea to monitor.

``def monitor_call(self, mea, kwargs)``
    This method must either return boolean value 'True', if MEA is healthy.
    Otherwise it should return an event string like 'failure' or
    'calls-capacity-reached' based on specific MEA health condition. More
    details on these event is given in below section.

Custom events
--------------
As mentioned in above section, if the return value of monitor_call method is
other than boolean value 'True', then we have to map those event to the
corresponding action as described below.

For example:

::

  vdu1:
    monitoring_policy:
      ping:
        actions:
          failure: respawn

In this  example, we have an event called 'failure'. So whenever monitor_call
returns 'failure' apmec will respawn the MEA.


Actions
--------
The available actions that a monitor driver can call when a particular event
occurs.

#. respawn
#. log

How to write TOSCA template to monitor MEA entities
----------------------------------------------------

In the vdus section, under vdu you can specify the monitors details with
corresponding actions and parameters.The syntax for writing monitor policy
is as follows:

::

  vduN:
    monitoring_policy:
      <monitoring-driver-name>:
        monitoring_params:
          <param-name>: <param-value>
          ...
        actions:
          <event>: <action-name>
          ...
      ...


Example Template
----------------

::

  vdu1:
    monitoring_policy:
      ping:
        actions:
          failure: respawn

  vdu2:
    monitoring_policy:
      http-ping:
        monitoring_params:
          port: 8080
          url: ping.cgi
        actions:
          failure: respawn

    acme_scaling_driver:
      monitoring_params:
        resource: cpu
        threshold: 10000
      actions:
        max_foo_reached: scale_up
        min_foo_reached: scale_down

