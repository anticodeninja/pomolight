#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pomolight.base import *
from serial import Serial

class Module(PomoModule):

    def __init__(self, core, config):
        super().__init__(core, config)
        self.port = Serial(config['port'], config['baud_rate'], timeout=1)

    def get_priority(self):
        return BACKGROUND_WORKER

    def state_changed(self):
        code = self.core.state.code
        while True:
            self.port.write(str(code).encode('ascii'))
            result = self.port.read(1)
            if int(result.decode('ascii')) == code: break
            time.sleep(0.1)

    def stop(self):
        self.port.close()
