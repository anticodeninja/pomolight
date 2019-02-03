#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import threading

try:
    import readline
except:
    pass

from pomolight.base import *

class Module(PomoModule):

    def __init__(self, core, config):
        super().__init__(core, config)
        self.silent = False

    def get_priority(self):
        return CLI_WORKER

    def state_changed(self):
        if self.core.state.scheduled_time:
            print('Switched to', self.core.state.activity, 'state until', self.core.state.scheduled_time)
        else:
            print('Switched to', self.core.state.activity, 'state')

    def start(self, blocked):
        if blocked:
            self.loop()
        else:
            self.thread = threading.Thread(target=self.loop)
            self.thread.daemon = True
            self.thread.start()


    def loop(self):
        while True:
            try:
                self.interact()
            except KeyboardInterrupt:
                print("\rQuiting...")
                self.core.stop()
                return
            except Exception as ex:
                print(ex)


    def interact(self):
        command = input()
        args = command.split(' ')
        args[0] = args[0].lower()

        if args[0] == 'work' or args[0] == 'rest':
            self.core.update(**parse_state_command(command))

        elif args[0] == 'reset':
            self.core.update(scheduled_time=None)

        elif args[0] == 'help':
            print('work [<time>] - set work state (with timer)')
            print('rest [<time>] - set rest state (with timer)')
            print('reset - reset current timer')
            print('help - shows this help')
            print('set <code> - (system) force set coded light')
            print('ding - (system) play ding sound')
            print('')
            print('<time> can be specified in delta form like: +25m +120s +20 +1:30, or in')
            print('absolute (masked) form like: :00: (if now is 12:15 it will be converted to 13:00).')
            print('When <time> is not set traflight will be switcher, but timer will not be set.')
            print('<code> is bitmasked value for RYG leds.')

        elif args[0] == 'set':
            self.core.update(
                code=int(args[1]),
                activity='forced color',
                scheduled_time=None)

        elif args[0] == 'ding':
            self.core.update()
