#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import tornado
import tornadoredis
import sockjs
import json
import random
from sockjs.tornado import SockJSConnection, SockJSRouter
from tornado import httpserver
from datetime import timedelta

connections = dict()
#subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())

def on_message(message):
    subscribers = connections.get(message.channel, [])
    for conn in subscribers:
        conn.send(message.body)

redis_client = tornadoredis.Client()
redis_client.connect()
redis_client.subscribe("notif", lambda message: redis_client.listen(on_message))


redis_publish_client = tornadoredis.Client()
redis_publish_client.connect()


class SockJSServer(SockJSConnection):
    def on_open(self, request):
        self.send(json.dumps({"text": "Welcome!"}))

    def on_message(self, message):
        print "Receive message: " + message
        data = json.loads(message)
        if(data.get("type") == "subscribe"):
            subscribers = connections.get(data["channel"], [])
            subscribers.append(self)
            connections[data["channel"]] = subscribers

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

    application = tornado.web.Application(urls,
        template_path=os.path.join(os.path.abspath(__file__).rsplit("/")[0], "www"))
    application.listen(3000)
    dummy_publish()
    tornado.ioloop.IOLoop.instance().start();
