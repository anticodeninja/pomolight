#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pomolight.base import *

import asyncio
import json
import threading
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.platform.asyncio

PAGE_DATA = open(os.path.join(HERE, "pomolight.html"), 'r').read()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(PAGE_DATA)


class ApiHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, module):
        self.module = module

    def open(self):
        self.module.subscribe(self)

    def on_close(self):
        self.module.unsubscribe(self)


class Module(PomoModule):

    def __init__(self, core, config):
        super().__init__(core, config)

        self.sockets = []
        self.ioloop = None
        self.app = tornado.web.Application([
            (r'/', MainHandler),
            (r'/api', ApiHandler, dict(module=self)),
        ])

    def get_priority(self):
        return IOLOOP_WORKER

    def start(self, blocked):
        if blocked:
            self.loop()
        else:
            asyncio.set_event_loop_policy(
                tornado.platform.asyncio.AnyThreadEventLoopPolicy())

            self.thread = threading.Thread(target=self.loop)
            self.thread.daemon = True
            self.thread.start()

    def state_changed(self):
        self.send_info(self.sockets)

    def stop(self):
        self.ioloop.stop()

    def subscribe(self, socket):
        self.sockets.append(socket)
        self.send_info([socket])

    def unsubscribe(self, socket):
        self.sockets.remove(socket)

    def send_info(self, sockets):
        if len(sockets) == 0:
            return

        state = self.core.state
        scheduled_time = None
        if state.scheduled_time:
            scheduled_time = state.scheduled_time.isoformat()

        info = json.dumps({
            'code': state.code,
            'activity': state.activity,
            'scheduled_time': scheduled_time,
        })

        for socket in sockets:
            socket.write_message(info)

    def loop(self):
        self.app.listen(self.config['port'])
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()
        self.core.stop()
