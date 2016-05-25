from bot import ConsulBot
from api import Partner
import redis
import json
import sys

print(sys.argv)
r = redis.Redis()
questions = json.load(open('questions.json', 'r'))
bot = ConsulBot(r, questions)
partner = Partner(sys.argv[1])

while True:
    text = input(">>>")
    bot.handle(text, partner)
    for message in partner.read_messages():
        print(message)



