#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado
import tornadoredis
import sockjs
import json
import random
from sockjs.tornado import SockJSConnection, SockJSRouter
from tornado import httpserver
from datetime import timedelta

connections = set()
#subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())

def on_message(message):
    print message
    for conn in connections:
        conn.send(message.body)

redis_client = tornadoredis.Client()
redis_client.connect()
#redis_client.subscribe("notif", lambda message: (conn.send(message) for conn in connections))
redis_client.subscribe("notif", lambda message: redis_client.listen(on_message))


redis_publish_client = tornadoredis.Client()
redis_publish_client.connect()


class SockJSServer(SockJSConnection):
    def on_open(self, request):
        self.send(json.dumps({"text": "Welcome!"}))
        connections.add(self)

    def on_message(self, message):
        pass

    def on_close(self):
        connections.remove(self)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index0.html")

def dummy_publish():
    redis_publish_client.publish("notif", "Generate random no " + str(random.randint(1, 100)))
    tornado.ioloop.IOLoop.instance().add_timeout(timedelta(seconds=5), dummy_publish)


if __name__ == "__main__":
    sockjs_router = SockJSRouter(
        SockJSServer, prefix="/_sockjs",
        user_settings={
            "sockjs_url": "http://cdn.jsdelivr.net/sockjs/1.0.1/sockjs.min.js"
    })
    urls = [
        (r"/", IndexHandler),
    ] + sockjs_router.urls

    application = tornado.web.Application(urls, template_path="../www")
    application.listen(3000)
    dummy_publish()
    tornado.ioloop.IOLoop.instance().start();
