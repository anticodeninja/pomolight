#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from simpleaudio import WaveObject
import os

from pomolight.base import *

DING_FILE = os.path.join(HERE, "ding.wav")

class Module(PomoModule):

    def __init__(self, core, config):
        super().__init__(core, config)
        self.ding = WaveObject.from_wave_file(DING_FILE)

    def get_priority(self):
        return BACKGROUND_WORKER

    def state_changed(self):
        self.ding.play()
