#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a simple echo bot using decorators and webhook with http.server
# It echoes any incoming text messages and does not use the polling method.

import http.server
import ssl
import telebot
import logging

import settings
from bot import ConsulBot
import json
import redis

# settings example:
# API_TOKEN = '<api_token>'
#
# WEBHOOK_HOST = '<ip/host where the bot is running>'
# WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
# WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr
#
# WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
# WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key
#
# # Quick'n'dirty SSL certificate generation:
# #
# # openssl genrsa -out webhook_pkey.pem 2048
# # openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
# #
# # When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# # with the same value in you put in WEBHOOK_HOST
#
# WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
# WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)


logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(settings.API_TOKEN)


# WebhookHandler, process webhook calls
class WebhookHandler(http.server.BaseHTTPRequestHandler):
    server_version = "WebhookHandler/1.0"

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == settings.WEBHOOK_URL_PATH and \
           'content-type' in self.headers and \
           'content-length' in self.headers and \
           self.headers['content-type'] == 'application/json':
            json_string = self.rfile.read(int(self.headers['content-length']))
            json_string = json_string.decode('utf8')

            self.send_response(200)
            self.end_headers()

            update = telebot.types.Update.de_json(json_string)
            bot.process_new_messages([update.message])
        else:
            self.send_error(403)
            self.end_headers()

r = redis.Redis()
questions = json.load(open('questions.json', 'r', encoding='utf8'))
consul_bot = ConsulBot(r, questions, bot)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hi there, I am EchoBot.\n"
                  "I am here to echo your kind words back to you."))


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    try:
        consul_bot.handle(message.text, message.chat.id)
    except Exception as e:
        logger.exception(e)
        #print(ex)
    #print(message.chat.id)
    #bot.send_message(message.chat.id, message.text)


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url=settings.WEBHOOK_URL_BASE + settings.WEBHOOK_URL_PATH,
                certificate=open(settings.WEBHOOK_SSL_CERT, 'r'))

# Start server
httpd = http.server.HTTPServer((settings.WEBHOOK_LISTEN, settings.WEBHOOK_PORT),
                                  WebhookHandler)

httpd.socket = ssl.wrap_socket(httpd.socket,
                               certfile=settings.WEBHOOK_SSL_CERT,
                               keyfile=settings.WEBHOOK_SSL_PRIV,
                               server_side=True)

httpd.serve_forever()
