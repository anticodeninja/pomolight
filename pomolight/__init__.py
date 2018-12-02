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
import yaml

try:
    import readline
except:
    pass

from functools import reduce

CONFIG_NAME = os.path.join(os.path.expanduser('~'), '.config', 'pomolight')
PRECISION = 5
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

config = None

here = os.path.abspath(os.path.dirname(__file__))
ding = simpleaudio.WaveObject.from_wave_file(os.path.join(here, "ding.wav"))

is_running = True
serial_port = None
ascii_art = False
actions = []
timer = None

class TimerAction:

    def __init__(self, target_datetime, action):
        self.target_datetime = target_datetime
        self.action = action


TERM_COLOR = {
    'W': lambda: print('\033[39m', end=''),
    'R': lambda: print('\033[31m', end=''),
    'Y': lambda: print('\033[33m', end=''),
    'G': lambda: print('\033[32m', end=''),
}

def set_color(code):
    if ascii_art:
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

    if serial_port:
        while True:
            serial_port.write(str(code).encode('ascii'))
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
        set_color(4 if work_timer else 1)
        if len(command) > 1:
            target_datetime = get_datetime(datetime.datetime.now(), command[1])
            actions.append(TimerAction(
                target_datetime,
                lambda: ding.play()))
            actions.append(TimerAction(
                target_datetime,
                lambda: set_color(6 if work_timer else 2)))
            actions.append(TimerAction(
                target_datetime,
                lambda: print('Timer for', command[0], 'activity is finished')))
            print('Switched to', command[0], 'state until', target_datetime)
        else:
            print('Switched to', command[0], 'state')

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
        set_color(int(command[1]))
        print('Force set: ', command[1])

    elif command[0] == 'ding':
        ding.play()


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


def load_config():
    global config

    try:
        with open(CONFIG_NAME, 'r', encoding='utf-8') as stream:
            config = yaml.load(stream)
        return
    except Exception:
        pass

    print('Configuration file was not found, lets try generate new one:')
    config = dict()

    if read_or_die('Do you want enable ASCII art [*yes*,no]', True, parser_y_or_n):
        config['ascii'] = True

    if read_or_die('Do you want enable COM adapter [yes,*no*]', False, parser_y_or_n):
        config['com'] = {
            'port': read_or_die('COM Port [*/dev/tty3*]', '/dev/tty3'),
            'baud_rate': read_or_die('BaudRate [*9600*]', 9600, int),
        }

    os.makedirs(os.path.dirname(CONFIG_NAME), exist_ok=True)
    with open(CONFIG_NAME, 'w', encoding='utf-8') as stream:
        yaml.dump(config, stream)


def main():
    global ascii_art
    global serial_port
    global is_running

    load_config()

    if 'ascii' in config:
        ascii_art = True

    if 'com' in config:
        serial_port = serial.Serial(
            config['com']['port'],
            config['com']['baud_rate'],
            timeout=1)

    print('Pomolight is running...')

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
    if serial_port:
        serial_port.close()

if __name__ == '__main__':
    main()

