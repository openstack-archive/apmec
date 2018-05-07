*******************
Apmec API Overview
*******************

Apmec API provides REST API end-points based on `ETSI MEC MANO standards`_.
The two new resources introduced are 'mead' and 'mea' for
describing the 'mem' extension. The resources request and response formats are
described in below sections.

.. _ETSI MEC MANO standards: http://www.etsi.org/deliver/etsi_gs/MEC-MAN/001_099/001/01.01.01_60/gs_mec-man001v010101p.pdf

API versions
============

Lists information for Apmec API version.

**GET /**

List API versions - Lists information about Apmec API version.

::

    Response:
    {
        "versions": [
            {
                "status": "CURRENT",
                "id": "v1.0",
                "links": [
                    {
                        "href": "http://10.18.160.13:9896/v1.0",
                        "rel": "self"
                    }
                ]
            }
        ]
    }

Meads
=====

**GET /v1.0/meads**

List meads - List meads stored in the MEA catalog.

::

    Response:
    {
        "meads": [
            {
                "service_types": [
                    {
                        "service_type": "mead",
                        "id": "378b774d-89f5-4634-9c65-9c49ed6f00ce"
                    }
                ],
                "description": "OpenWRT with services",
                "tenant_id": "4dd6c1d7b6c94af980ca886495bcfed0",
                "mgmt_driver": "openwrt",
                "infra_driver": "",
                "attributes": {
                    "mead": "template_name: OpenWRT\r\ndescription:
                    template_description <sample_mead_template>"
                },
                "id": "247b045e-d64f-4ae0-a3b4-8441b9e5892c",
                "name": "openwrt_services"
            }
        ]
    }

**GET /v1.0/meads/{mead_id}**

Show mead - Show information for a specified mead id.

::

    Response:
    {
        "mead": {
            "service_types": [
                {
                    "service_type": "mead",
                    "id": "378b774d-89f5-4634-9c65-9c49ed6f00ce"
                }
            ],
            "description": "OpenWRT with services",
            "tenant_id": "4dd6c1d7b6c94af980ca886495bcfed0",
            "mgmt_driver": "openwrt",
            "infra_driver": "",
            "attributes": {
                "mead": "template_name: OpenWRT\r\ndescription:
                template_description <sample_mead_template>"
            },
            "id": "247b045e-d64f-4ae0-a3b4-8441b9e5892c",
            "name": "openwrt_services"
        }
    }

**POST /v1.0/meads**

Create mead - Create a mead entry based on the mead template.

::

    Request:
    {
        "auth": {
            "tenantName": "admin",
            "passwordCredentials": {
                "username": "admin",
                "password": "devstack"
            }
        },
        "mead": {
            "service_types": [{"service_type": "mead"}],
            "tenant_id": "bb6a3be1021a4746ab727a6c9296e797",
            "description": "OpenWRT router",
            "attributes": {
                "mead": "description: OpenWRT with services\nmetadata: {template_name: OpenWRT}\ntopology_template:\n  node_templates:\n    CP1:\n      properties: {anti_spoofing_protection: false, management: true, order: 0}\n      requirements:\n      - virtualLink: {node: VL1}\n      - virtualBinding: {node: VDU1}\n      type: tosca.nodes.mec.CP.Apmec\n    CP2:\n      properties: {anti_spoofing_protection: false, order: 1}\n      requirements:\n      - virtualLink: {node: VL2}\n      - virtualBinding: {node: VDU1}\n      type: tosca.nodes.mec.CP.Apmec\n    CP3:\n      properties: {anti_spoofing_protection: false, order: 2}\n      requirements:\n      - virtualLink: {node: VL3}\n      - virtualBinding: {node: VDU1}\n      type: tosca.nodes.mec.CP.Apmec\n    VDU1:\n      capabilities:\n        mec_compute:\n          properties: {disk_size: 1 GB, mem_size: 512 MB, num_cpus: 1}\n      properties:\n        config: 'param0: key1\n\n          param1: key2\n\n          '\n        image: OpenWRT\n        mgmt_driver: openwrt\n        monitoring_policy:\n          actions: {failure: respawn}\n          name: ping\n          parameters: {count: 3, interval: 10}\n      type: tosca.nodes.mec.VDU.Apmec\n    VL1:\n      properties: {network_name: net_mgmt, vendor: Apmec}\n      type: tosca.nodes.mec.VL\n    VL2:\n      properties: {network_name: net0, vendor: Apmec}\n      type: tosca.nodes.mec.VL\n    VL3:\n      properties: {network_name: net1, vendor: Apmec}\n      type: tosca.nodes.mec.VL\ntosca_definitions_version: tosca_simple_profile_for_mec_1_0_0\n"
            },
            "name": "OpenWRT"
        }
    }

::

    Response:
    {
       "mead": {
           "service_types": [
               {
                   "service_type": "mead",
                   "id": "336fe422-9fba-47c7-87fb-d48475c3e0ce"
               }
           ],
           "description": "OpenWRT router",
           "tenant_id": "4dd6c1d7b6c94af980ca886495bcfed0",
           "mgmt_driver": "noop",
           "infra_driver": "",
           "attributes": {
               "mead": "template_name: OpenWRT \r\ndescription:
               template_description <sample_mead_template>"
           },
           "id": "ab10a543-22ee-43af-a441-05a9d32a57da",
           "name": "OpenWRT"
       }
    }

**DELETE /v1.0/meads/{mead_id}**

Delete mead - Deletes a specified mead_id from the MEA catalog.

This operation does not accept a request body and does not return a response
body.

Meas
====

**GET /v1.0/meas**

List meas - Lists instantiated meas in MEA Manager.

::

    Response:
    {
        "meas": [
            {
                "status": "ACTIVE",
                "name": "open_wrt",
                "tenant_id": "4dd6c1d7b6c94af980ca886495bcfed0",
                "instance_id": "f7c93726-fb8d-4036-8349-2e82f196e8f6",
                "mgmt_url": "{\"vdu1\": \"192.168.120.3\"}",
                "attributes": {
                    "service_type": "firewall",
                    "param_values": "",
                    "heat_template": "description: sample_template_description
                        type: OS::Nova::Server\n",
                    "monitoring_policy": "noop",
                    "failure_policy": "noop"
                },
                "id": "c9b4f5a5-d304-473a-a57e-b665b1f9eb8f",
                "description": "OpenWRT with services"
            }
        ]
    }

**GET /v1.0/meas/{mea_id}**

Show mea - Show information for a specified mea_id.

::

    Response:
    {
        "mea": [
            {
                "status": "ACTIVE",
                "name": "open_wrt",
                "tenant_id": "4dd6c1d7b6c94af980ca886495bcfed0",
                "instance_id": "f7c93726-fb8d-4036-8349-2e82f196e8f6",
                "mgmt_url": "{\"vdu1\": \"192.168.120.3\"}",
                "attributes": {
                    "service_type": "firewall",
                    "param_values": "",
                    "heat_template": "description: OpenWRT with services\n
                    sample_template_description    type: OS::Nova::Server\n",
                    "monitoring_policy": "noop", "failure_policy": "noop"
                },
                "id": "c9b4f5a5-d304-473a-a57e-b665b1f9eb8f",
                "description": "OpenWRT with services"
            }
        ]
    }

**POST /v1.0/meas**

Create mea - Create a mea based on the mead template id.

::

    Request:
    {
        "auth": {
            "tenantName": "admin",
            "passwordCredentials": {
                "username": "admin",
                "password": "devstack"
            }
        },
        "mea": {
            "attributes": {},
            "vim_id": "",
            "description": "demo-example",
            "mead_id": "ad0c2c7c-825e-43c5-a402-b5710902b408",
            "name": "demo-mea"
        }
    }

::

    Response:
    {
        "mea": {
            "status": "PENDING_CREATE",
            "description": "demo-example",
            "tenant_id": "bb6a3be1021a4746ab727a6c9296e797",
            "vim_id": "c91413b9-eaf9-47f7-86b6-3f3a3e29261e",
            "name": "demo-mea",
            "instance_id": "050f4d0e-ff7c-4a5d-9dba-dbe238b3348b",
            "mgmt_url": null,
            "placement_attr": {
                "vim_name": "VIM0"
            },
            "error_reason": null,
            "attributes": {
                "service_type": "firewall",
                "heat_template": "description: OpenWRT with services\n
                <sample_heat_template> type: OS::Nova::Server\n",
                "monitoring_policy": "noop",
                "failure_policy": "noop"
            },
            "id": "e3158513-92f4-4587-b949-70ad0bcbb2dd",
            "mead_id": "247b045e-d64f-4ae0-a3b4-8441b9e5892c"
        }
    }

**PUT /v1.0/meas/{mea_id}**

Update mea - Update a mea based on user config file or data.

::

    Request:
    {
        "auth": {
            "tenantName": "admin",
            "passwordCredentials": {
                "username": "admin",
                "password": "devstack"
            }
        },
        "mea": {
            "attributes": {
                "config": "vdus:\n  vdu1: <sample_vdu_config> \n\n"
            }
        }
    }

::

    Response:
    {
        "mea": {
            "status": "PENDING_UPDATE",
            "name": "",
            "tenant_id": "4dd6c1d7b6c94af980ca886495bcfed0",
            "instance_id": "4f0d6222-afa0-4f02-8e19-69e7e4fd7edc",
            "mgmt_url": "{\"vdu1\": \"192.168.120.4\"}",
            "attributes": {
                "service_type": "firewall",
                "monitoring_policy": "noop",
                "config": "vdus:\n  vdu1:\n    config: {<sample_vdu_config>
                 type: OS::Nova::Server\n",
                "failure_policy": "noop"
            },
            "id": "e3158513-92f4-4587-b949-70ad0bcbb2dd",
            "description": "OpenWRT with services"
        }
    }

**DELETE /v1.0/meas/{mea_id}**

Delete mea - Deletes a specified mea_id from the MEA list.
