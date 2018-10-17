# apmec
This project aims at building an automated provisioning framework for Multi-access Edge Computing (MEC) based on OpenStack platform


Current features of APMEC are to:

- orchestrate the MEC services

- leverage MANO's API to allow the reuse of NF network services (currently use OpenStack Tacker - NFV Orchestration service) for MEC services

- support multi-MANO features that offer the scalability and improve resource utilization of MEC services. 

- manage the life-cycle of MEC applications (creation, update, delete)

- monitor MEC applications

- scale in/out MEC applications


On-going features:

- fast live migration in order to support mobility in MEC

- state management for the stateful MEC applications

- acceleration technologies like DPDK, VPP, FPGA,...

- container technologies


**Acronym**:


MEP: MEC Platform

MESO: MEC Service Orchestrator

MES: MEC service

MEO: MEC Orchestrator

MEM: MEC Manager

MEA: MEC Application

MEAD: MEA Descriptor

Authors:

Deutsche Telekom Chair of Communication Networks,

Technical University of Dresden, Germany.
