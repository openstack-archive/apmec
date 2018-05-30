#!/usr/bin/env python

# Copyright 2011 VMware, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# If ../apmec/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in
# /usr/(local/)tosca_lib/python...

import sys

from oslo_config import cfg
import oslo_i18n
from oslo_service import service as common_service

from apmec import _i18n
_i18n.enable_lazy()
from apmec.common import config
from apmec import service


oslo_i18n.install("apmec")


def main():
    # the configuration will be read into the cfg.CONF global data structure
    config.init(sys.argv[1:])
    if not cfg.CONF.config_file:
        sys.exit(_("ERROR: Unable to find configuration file via the default"
                   " search paths (~/.apmec/, ~/, /etc/apmec/, /etc/) and"
                   " the '--config-file' option!"))

    try:
        apmec_api = service.serve_wsgi(service.ApmecApiService)
        launcher = common_service.launch(cfg.CONF, apmec_api,
                                         workers=cfg.CONF.api_workers or None)
        launcher.wait()
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        sys.exit(_("ERROR: %s") % e)
