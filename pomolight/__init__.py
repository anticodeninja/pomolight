#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import importlib
import json
import os
import sys
import time
import threading

from pomolight.base import *

class State:

    def __init__(self):
        self.code = 0
        self.activity = None
        self.scheduled_time = None
        self.scheduled_code = 0
        self.scheduled_activity = None

    def update(self, **kwargs):
        self.code = kwargs.get('code', self.code)
        self.activity = kwargs.get('activity', self.activity)
        self.scheduled_time = kwargs.get('scheduled_time', self.scheduled_time)
        if self.scheduled_time:
            self.scheduled_code = kwargs.get('scheduled_code', self.scheduled_code)
            self.scheduled_activity = kwargs.get('scheduled_activity', self.scheduled_activity)
        else:
            self.scheduled_code = None
            self.scheduled_activity = None

    def test(self, time):
        return self.scheduled_time and time >= self.scheduled_time


class Pomolight:

    def __init__(self):
        self.load_config()

        self.is_closing = threading.Event()
        self.state = State()
        self.modules = []


    def load_config(self):
        try:
            with open(CONFIG_NAME, 'r', encoding='utf-8') as stream:
                self.config = json.load(stream)
            return
        except Exception:
            pass

        print('Configuration file was not found, lets try generate new one:')
        self.config = dict()
        deps = []

        if read_or_die('Do you want enable interactive cli [*yes*,no]', True, parser_y_or_n):
            self.config['cli'] = {}

        if read_or_die('Do you want enable ding sound [*yes*,no]', True, parser_y_or_n):
            deps.append('simpleaudio')
            self.config['sound'] = {}

        if read_or_die('Do you want enable ASCII art [*yes*,no]', True, parser_y_or_n):
            self.config['ascii'] = {}

        if read_or_die('Do you want enable trayicon [*yes*,no]', True, parser_y_or_n):
            deps.append('pystray')
            self.config['tray'] = {
                'commands': [
                    read_or_die('Command for "work" [work +25m]', 'work +25m'),
                    read_or_die('Command for "rest" [rest +5m]', 'rest +5m'),
                ]
            }

        if read_or_die('Do you want enable COM adapter [yes,*no*]', False, parser_y_or_n):
            deps.append('pyserial')
            self.config['comadapter'] = {
                'port': read_or_die('COM Port [*/dev/tty3*]', '/dev/tty3'),
                'baud_rate': read_or_die('BaudRate [*9600*]', 9600, int),
            }

        if read_or_die('Do you want enable WEB adapter [yes,*no*]', False, parser_y_or_n):
            deps.append('tornado')
            self.config['web'] = {
                'port': read_or_die('WEB Port [*13001*]', 13001, int),
            }

        os.makedirs(os.path.dirname(CONFIG_NAME), exist_ok=True)
        with open(CONFIG_NAME, 'w', encoding='utf-8') as stream:
            json.dump(self.config, stream)

        if len(deps) > 0:
            print('The following dependencies are required: {}'.format(', '.join(deps)))
            print('Please install them with: "pip install {}"'.format(' '.join(deps)))
            sys.exit()


    def start(self):
        for name, config in self.config.items():
            try:
                namespace = importlib.import_module('pomolight.'+name)
                module = namespace.Module(self, config)
                self.modules.append(module)
            except Exception as e:
                print('Cannot initialize {}: {}'.format(name, e))

        self.modules.sort(key=lambda x: x.get_priority())
        if len(self.modules) == 0 or \
           self.modules[-1].get_priority() == BACKGROUND_WORKER:
            raise Exception('There should be at least one interactive worker')

        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self.thread.start()

        for module in self.modules[:-1]:
            module.start(False)
        self.modules[-1].start(True)


    def update(self, **kwargs):
        self.state.update(**kwargs)
        for module in self.modules:
            module.state_changed()


    def stop(self):
        self.is_closing.set()
        for module in self.modules:
            module.stop()


    def loop(self):
        while not self.is_closing.wait(PRECISION):
            if not self.state.test(datetime.datetime.now()):
                continue

            self.update(
                code=self.state.scheduled_code,
                activity=self.state.scheduled_activity,
                scheduled_time=None
            )

def main():
    print('Pomolight is starting...')
    Pomolight().start()


if __name__ == '__main__':
    main()

