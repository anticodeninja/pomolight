#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import reduce
import datetime
import os

BACKGROUND_WORKER = 0
IOLOOP_WORKER = 1
CLI_WORKER = 2
UI_WORKER = 3

HERE = os.path.abspath(os.path.dirname(__file__))
CONFIG_NAME = os.path.join(os.path.expanduser('~'), '.config', 'pomolight')
PRECISION = 5

class PomoModule:

    def __init__(self, core, config):
        self.core = core
        self.config = config

    def get_priority(self):
        return BACKGROUND_WORKER

    def start(self, blocked):
        pass

    def state_changed(self):
        pass

    def stop(self):
        pass


def parser_y_or_n(result):
    if result in ['y', 'yes']: return True
    if result in ['n', 'no']: return False
    raise Exception('Input should be "y", "yes", "n" or "no"')


def read_or_die(message, default=None, parser=None):
    while True:
        print(message + ': ', end='')
        result = input()
        try:
            if not result.strip() and default is not None:
                return default
            return parser(result) if parser else result
        except Exception as e:
            print('Incorrect input: {}, lets try again...'.format(e))


def get_datetime(now, value):
    """Delta form: +1h +25m +120s +20 +1:30 +1:30:30
    Absolute form: :20, 12:20, ::0, 12:20:30, :20:, 12::"""

    now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)

    if value.startswith('+'):
        if value.endswith('h'):
            value = [float(value[1:-1]), 0, 0]
        elif value.endswith('m'):
            value = [0, float(value[1:-1]), 0]
        elif value.endswith('s'):
            value = [0, 0, float(value[1:-1])]
        else:
            value = [float(x) if len(x) > 0 else 0 for x in value[1:].split(':')]
            if len(value) == 1:
                value = [0, value[0], 0]
            elif len(value) == 2:
                value = [0, value[0], value[1]]

        return now + datetime.timedelta(seconds=reduce(lambda s, x: s * 60 + x, value))

    else:
        value = [float(x) if len(x)>0 else None for x in value.split(':')]
        if len(value) == 1:
            value = [None, value[0], None]
        elif len(value) == 2:
            value = [value[0], value[1], None]

        for i, x in enumerate(value):
            value[i] = x if x is not None or i == 0 or value[i-1] is None else 0.0

        if value[2] is not None and value[2] != now.second:
            now = now + datetime.timedelta(seconds=(60 if value[2] < now.second else 0) + value[2] - now.second)
        if value[1] is not None and value[1] != now.minute:
            now = now + datetime.timedelta(minutes=(60 if value[1] < now.minute else 0) + value[1] - now.minute)
        if value[0] is not None and value[0] != now.hour:
            now = now + datetime.timedelta(hours=(24 if value[0] < now.hour else 0) + value[0] - now.hour)

        return now
