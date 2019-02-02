#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pomolight.base import *

ASCII_ART = """
       _______
 ___  /  ___  \  ___
\   | | /RRR\ | |   /
 \  | | RRRRR | |  /
  \_| | \RRR/ | |_/
 ___  |  ___  |  ___
\   | | /YYY\ | |   /
 \  | | YYYYY | |  /
  \_| | \YYY/ | |_/
 ___  |  ___  |  ___
\   | | /GGG\ | |   /
 \  | | GGGGG | |  /
  \_| | \GGG/ | |_/
      \_______/
         | |
         | |
         | |
         | |
         | |
___\_____| |____\\___
 ^    ^            ^
""";

TERM_COLOR = {
    'W': lambda: print('\033[39m', end=''),
    'R': lambda: print('\033[31m', end=''),
    'Y': lambda: print('\033[33m', end=''),
    'G': lambda: print('\033[32m', end=''),
}


class Module(PomoModule):

    def __init__(self, core, config):
        super().__init__(core, config)

    def get_priority(self):
        return BACKGROUND_WORKER

    def state_changed(self):
        code = self.core.state.code
        current_color = 'W'
        for char in ASCII_ART:
            target_color = char if char in TERM_COLOR else 'W'
            if current_color != target_color:
                TERM_COLOR[target_color]()
                current_color = target_color

            if char == 'R':
                char = 'O' if code & 4 else ' '
            elif char == 'Y':
                char = 'O' if code & 2 else ' '
            elif char == 'G':
                char = 'O' if code & 1 else ' '

            print(char, end='')

