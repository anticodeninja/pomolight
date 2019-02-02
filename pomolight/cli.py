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
        if self.silent:
            return
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
        command = command.split(' ')
        command[0] = command[0].lower()

        if command[0] == 'work' or command[0] == 'rest':
            work_timer = command[0] == 'work'

            code=4 if work_timer else 1
            activity=command[0]

            if len(command) > 1:
                scheduled_time = get_datetime(datetime.datetime.now(), command[1])
                self.update(
                    code=code,
                    activity=command[0],
                    scheduled_time=scheduled_time,
                    scheduled_code=6 if work_timer else 2,
                    scheduled_activity='almost rest' if work_timer else 'almost work')
                print('Switched to', command[0], 'state until', scheduled_time)
            else:
                self.update(code=code, activity=command[0], scheduled_time=None)
                print('Switched to', command[0], 'state')

        elif command[0] == 'reset':
            self.update(scheduled_time=None)
            print('Reset current timer')

        elif command[0] == 'help':
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

        elif command[0] == 'set':
            self.update(
                code=int(command[1]),
                activity='forced color',
                scheduled_time=None)
            print('Force set: ', command[1])

        elif command[0] == 'ding':
            self.update()

    def update(self, **kwargs):
        self.silent = True
        self.core.update(**kwargs)
        self.silent = False
