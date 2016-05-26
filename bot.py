import json
import random
from telebot import types


class ConsulBot:
    CURRENT_QUESTION = 'current_question'
    ASKED = "asked_{}"

    QUESTION_KEY_FOR_COMMAND = {
        'odpowiedź': 'answer',
        'вопрос на русском': 'rus_question',
        'ответ на русском': 'rus_answer',
    }
    COMMANDS = list(QUESTION_KEY_FOR_COMMAND.keys())

    markup = types.ReplyKeyboardMarkup()
    markup.row(*COMMANDS)

    def __init__(self, redis, questions, api):
        self.redis = redis
        self.api = api
        self.questions_ids = [q['id'] for q in questions]
        self.questions_ids_set = set(self.questions_ids)
        self.questions = dict(zip(self.questions_ids, questions))

    def handle(self, text, chat_id):
        if self.redis.hexists(self.CURRENT_QUESTION, chat_id):
            command = text.strip().lower()
            if command in self.COMMANDS:
                q = self._get_current_question(chat_id)
                self.api.send_message(chat_id, q[self.QUESTION_KEY_FOR_COMMAND[command]])
                return

            correct = self.check_answer(text, chat_id)
            self.api.send_message(chat_id, ["błędnie", "poprawnie", "Nie wiem chy to poprawnie"][correct])
            if correct == 0:
                current_question = self._get_current_question(chat_id)
                self.api.send_message(chat_id, current_question['answer'])
        self._ask_new_question(chat_id)

    def _get_current_question(self, chat_id):
        current_question_id = int(self.redis.hget(self.CURRENT_QUESTION, chat_id))
        return self.questions[current_question_id]

    def check_answer(self, text, chat_id):
        text = text.lower().strip()
        current_question = self._get_current_question(chat_id)
        if 'answer_check' not in current_question:
            return 2

        for word in current_question['answer_check'].split(','):
            if not any(synonym.strip() in text for synonym in word.split(';')):
                return 0
        return 1

    def _ask_new_question(self, chat_id):
        question = self._get_not_asked_question(chat_id)
        self.redis.hset(self.CURRENT_QUESTION, chat_id, question['id'])
        self.api.send_message(chat_id, question['question'], reply_markup=self.markup)

    def _get_not_asked_question(self, chat_id):
        asked_question_ids = {int(x) for x in self.redis.smembers(self.ASKED.format(chat_id))}
        not_asked = self.questions_ids_set - asked_question_ids
        if not not_asked:
            self.redis.delete(self.ASKED.format(chat_id))
            not_asked = self.questions_ids_set
        question_id = random.choice(list(not_asked))
        self.redis.sadd(self.ASKED.format(chat_id), question_id)
        return self.questions[question_id]
