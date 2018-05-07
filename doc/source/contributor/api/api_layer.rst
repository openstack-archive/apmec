Apmec WSGI/HTTP API layer
===========================

This section will cover the internals of Apmec's HTTP API, and the classes
in Apmec that can be used to create Extensions to the Apmec API.

Python web applications interface with webservers through the Python Web
Server Gateway Interface (WSGI) - defined in `PEP 333 <http://legacy.python.org/dev/peps/pep-0333/>`_

Startup
-------

Apmecs's WSGI server is started from the `server module <http://git.openstack.org/cgit/openstack/apmec/tree/apmec/service.py>`_
and the entry point `serve_wsgi` is called to build an instance of the
`ApmecApiService`_, which is then returned to the server module,
which spawns a `Eventlet`_ `GreenPool`_ that will run the WSGI
application and respond to requests from clients.


.. _ApmecApiService: http://git.openstack.org/cgit/openstack/apmec/tree/apmec/service.py

.. _Eventlet: http://eventlet.net/

.. _GreenPool: http://eventlet.net/doc/modules/greenpool.html

WSGI Application
----------------

During the building of the ApmecApiService, the `_run_wsgi` function
creates a WSGI application using the `load_paste_app` function inside
`config.py`_ - which parses `api-paste.ini`_ - in order to create a WSGI app
using `Paste`_'s `deploy`_.

The api-paste.ini file defines the WSGI applications and routes - using the
`Paste INI file format`_.

The INI file directs paste to instantiate the `APIRouter`_ class of
Apmec, which contains several methods that map MEC resources (such as
mead, mea) to URLs, and the controller for each resource.


.. _config.py: http://git.openstack.org/cgit/openstack/apmec/tree/apmec/common/config.py

.. _api-paste.ini: http://git.openstack.org/cgit/openstack/apmec/tree/etc/apmec/api-paste.ini

.. _APIRouter: http://git.openstack.org/cgit/openstack/apmec/tree/apmec/api/v1/router.py

.. _Paste: http://pythonpaste.org/

.. _Deploy: http://pythonpaste.org/deploy/

.. _Paste INI file format: http://pythonpaste.org/deploy/#applications

Further reading
---------------

Apmec wsgi is based on neutron's extension. The following doc is still
relevant.

`Yong Sheng Gong: Deep Dive into Neutron <http://www.slideshare.net/gongys2004/inside-neutron-2>`_
