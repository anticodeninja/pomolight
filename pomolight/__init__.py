#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import datetime
import json
import os
import serial
import simpleaudio
import yaml
import time
import threading
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.platform.asyncio

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
TERM_COLOR = {
    'W': lambda: print('\033[39m', end=''),
    'R': lambda: print('\033[31m', end=''),
    'Y': lambda: print('\033[33m', end=''),
    'G': lambda: print('\033[32m', end=''),
}

config = None

here = os.path.abspath(os.path.dirname(__file__))
ding = simpleaudio.WaveObject.from_wave_file(os.path.join(here, "ding.wav"))
webpage_data = open(os.path.join(here, "pomolight.html"), 'r').read()

is_closing = threading.Event()
serial_port = None
tornado_ioloop = None
tornado_sockets = []
ascii_art = False

current_code = 0
current_activity = None
next_activity_time = None


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(webpage_data)


class ApiHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        tornado_sockets.append(self)
        update_remote(self)

    def on_close(self):
        tornado_sockets.remove(self)


def update(code=None, activity=None):
    global current_code
    global current_activity

    if code:
        current_code = code
    if activity:
        current_activity = activity

    update_local()
    update_remote()


def update_local():
    if ascii_art:
        current_color = 'W'
        for char in ASCII_ART:
            target_color = char if char in TERM_COLOR else 'W'
            if current_color != target_color:
                TERM_COLOR[target_color]()
                current_color = target_color

            if char == 'R':
                char = 'O' if current_code & 4 else ' '
            elif char == 'Y':
                char = 'O' if current_code & 2 else ' '
            elif char == 'G':
                char = 'O' if current_code & 1 else ' '

            print(char, end='')

    if serial_port:
        while True:
            serial_port.write(str(current_code).encode('ascii'))
            result = serial_port.read(1)
            if int(result.decode('ascii')) == current_code: break
            time.sleep(0.1)


def update_remote(socket=None):
    sockets = [socket] if socket else tornado_sockets
    if len(sockets) == 0:
        return

    next_activity_time_iso = None
    if next_activity_time:
        next_activity_time_iso = next_activity_time.isoformat()

    info = json.dumps({
        'current_code': current_code,
        'current_activity': current_activity,
        'next_activity_time': next_activity_time_iso,
    })

    for socket in sockets:
        socket.write_message(info)


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
    global next_activity_time
    global next_activity_handler

    while not is_closing.wait(PRECISION):
        try:
            now = datetime.datetime.now()
            if next_activity_time and now >= next_activity_time:
                next_activity_time = None
                next_activity_handler()
                next_activity_handler = None

        except Exception:
            pass


def tornado_loop():
    global tornado_ioloop

    tornado_app = tornado.web.Application([
        (r'/', MainHandler),
        (r'/api', ApiHandler),
    ])
    tornado_app.listen(config['web']['port'])

    tornado_ioloop = tornado.ioloop.IOLoop.current()
    tornado_ioloop.start()


def main_loop():
    global next_activity_time
    global next_activity_handler

    command = input()
    command = command.split(' ')
    command[0] = command[0].lower()

    if command[0] == 'work' or command[0] == 'rest':
        work_timer = command[0] == 'work'

        if len(command) > 1:
            def __handler():
                ding.play()
                update(6 if work_timer else 2, 'almost rest' if work_timer else 'almost work')
                print('Timer for', command[0], 'activity is finished')
            next_activity_time = get_datetime(datetime.datetime.now(), command[1])
            next_activity_handler = __handler
            print('Switched to', command[0], 'state until', next_activity_time)
        else:
            next_activity_time = None
            next_activity_handler = None
            print('Switched to', command[0], 'state')

        update(4 if work_timer else 1, command[0])

    elif command[0] == 'reset':
        next_activity_time = None
        update()
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
        update(int(command[1]), 'forced color')
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

    if read_or_die('Do you want enable WEB adapter [yes,*no*]', False, parser_y_or_n):
        config['web'] = {
            'port': read_or_die('WEB Port [*13001*]', 13001, int),
        }

    os.makedirs(os.path.dirname(CONFIG_NAME), exist_ok=True)
    with open(CONFIG_NAME, 'w', encoding='utf-8') as stream:
        yaml.dump(config, stream)


def main():
    global ascii_art
    global serial_port
    global tornado_app

    load_config()

    if 'ascii' in config:
        ascii_art = True

    if 'com' in config:
        try:
            serial_port = serial.Serial(
                config['com']['port'],
                config['com']['baud_rate'],
                timeout=1)
        except:
            print('Cannot initialize COM port, ignore COM adapter')

    if 'web' in config:
        asyncio.set_event_loop_policy(tornado.platform.asyncio.AnyThreadEventLoopPolicy())
        tornado_thread = threading.Thread(target=tornado_loop)
        tornado_thread.daemon = True
        tornado_thread.start()

    print('Pomolight is running...')

    timer_thread = threading.Thread(target=timer_loop)
    timer_thread.daemon = True
    timer_thread.start()

    while not is_closing.is_set():
        try:
            main_loop()
        except KeyboardInterrupt:
            print("\rQuiting...")
            is_closing.set()
            if tornado_ioloop:
                tornado_ioloop.stop()
        except Exception as ex:
            print(ex)

    if serial_port:
        serial_port.close()

if __name__ == '__main__':
    main()

