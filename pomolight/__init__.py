#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import os
import serial
import simpleaudio
import time
import threading

try:
    import readline
except:
    pass

from functools import reduce

# TODO Make it configurable
PORT = 'COM7' #'/dev/ttyUSB0'
PRECISION = 1

here = os.path.abspath(os.path.dirname(__file__))
ding = simpleaudio.WaveObject.from_wave_file(os.path.join(here, "ding.wav"))

is_running = True
serial_port = None
actions = []
timer = None

class TimerAction:

    def __init__(self, target_datetime, action):
        self.target_datetime = target_datetime
        self.action = action

def set_color(code):
    while True:
        serial_port.write(code.encode('ascii'))
        result = serial_port.read(1)
        if result.decode('ascii') == code: break
        time.sleep(0.1)

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

def timer_loop():
    global is_running
    global actions

    while is_running:
        try:
            now = datetime.datetime.now()
            while len(actions) > 0 and now >= actions[0].target_datetime:
                actions[0].action()
                actions.pop(0)

        finally:
            time.sleep(PRECISION)

def main_loop():
    command = input()
    command = command.split(' ')
    command[0] = command[0].lower()

    if command[0] == 'work' or command[0] == 'rest':
        actions.clear()
        work_timer = command[0] == 'work'
        set_color('4' if work_timer else '1')
        if len(command) > 1:
            target_datetime = get_datetime(datetime.datetime.now(), command[1])
            actions.append(TimerAction(
                target_datetime,
                lambda: ding.play()))
            actions.append(TimerAction(
                target_datetime,
                lambda: set_color('6' if work_timer else '2')))
            print('Switched to', 'work' if work_timer else 'rest', 'state until', target_datetime)
        else:
            print('Switched to', 'work' if work_timer else 'rest', 'state')

    elif command[0] == 'reset':
        actions.clear()
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
        set_color(command[1])
        print('Force set: ', command[1])

    elif command[0] == 'ding':
        ding.play()


def main():
    global serial_port
    global is_running

    serial_port = serial.Serial(PORT, 9600, timeout=1)
    timer = threading.Thread(target=timer_loop)
    timer.start()

    while is_running:
        try:
            main_loop()
        except KeyboardInterrupt:
            print("\rQuiting...")
            is_running = False
        except Exception as ex:
            print(ex)

    timer.join()
    serial_port.close()

if __name__ == '__main__':
    main()

