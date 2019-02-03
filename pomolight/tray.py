#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from pomolight.base import *

SIZE = 32
BOX = ((1,1), (SIZE-2,SIZE-2))

class Module(PomoModule):

    def __init__(self, core, config):
        super().__init__(core, config)

        self.icon = Icon('pomolight')
        self.icon.icon = self.get_image(self.core.state.code)

        menu = [
            MenuItem(x, (lambda x: lambda: self.core.update(**parse_state_command(x)))(x))
            for x in self.config['commands']
        ]
        menu.append(MenuItem('exit', lambda: self.icon.stop()))
        self.icon.menu = Menu(*menu)

    def get_priority(self):
        return UI_WORKER

    def state_changed(self):
        self.icon.icon = self.get_image(self.core.state.code)

    def start(self, blocking):
        if not blocking:
            raise Exception('Non blocking mode is not supported')
        self.icon.run()

    def get_image(self, code):
        image = Image.new('RGBA', (SIZE,SIZE), (0, 0, 0, 0))

        colors = []
        if code & 4: colors.append('#dc322f')
        if code & 2: colors.append('#b58900')
        if code & 1: colors.append('#859900')
        if not(colors): colors.append('#fdf6e3')
        arc = 360 / len(colors)

        draw = ImageDraw.Draw(image)
        for i, color in enumerate(colors):
            draw.pieslice(BOX, i * arc, (i + 1) * arc, fill=color)

        return image
