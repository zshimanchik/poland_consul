import json
import random


class ConsulBot:
    CURRENT_QUESTION = 'current_question'
    ASKED = "asked_{}"

    QUESTION_KEY_FOR_COMMAND = {
        'odpowiedź': 'answer',
        'вопрос на русском': 'rus_question',
        'ответ на русском': 'rus_answer',
    }
    COMMANDS = list(QUESTION_KEY_FOR_COMMAND.keys())

    def __init__(self, redis, questions):
        self.redis = redis
        self.questions_ids = [q['id'] for q in questions]
        self.questions_ids_set = set(self.questions_ids)
        self.questions = dict(zip(self.questions_ids, questions))

    def handle(self, text, partner):
        if self.redis.hexists(self.CURRENT_QUESTION, partner.id):
            command = text.strip().lower()
            if command in self.COMMANDS:
                q = self._get_current_question(partner.id)
                partner.send_message(q[self.QUESTION_KEY_FOR_COMMAND[command]])
                return

            correct = self.check_answer(text, partner)
            partner.send_message(["błędnie", "poprawnie", "Nie wiem chy to poprawnie"][correct])
            if correct == 0:
                current_question = self._get_current_question(partner.id)
                partner.send_message(current_question['answer'])
        self._ask_new_question(partner)

    def _get_current_question(self, partner_id):
        current_question_id = int(self.redis.hget(self.CURRENT_QUESTION, partner_id))
        return self.questions[current_question_id]

    def check_answer(self, text, partner):
        text = text.lower().strip()
        current_question = self._get_current_question(partner.id)
        if 'answer_check' not in current_question:
            return 2

        for word in current_question['answer_check'].split(','):
            if not any(synonym.strip() in text for synonym in word.split(';')):
                return 0
        return 1

    def _ask_new_question(self, partner):
        question = self._get_not_asked_question(partner.id)
        self.redis.hset(self.CURRENT_QUESTION, partner.id, question['id'])
        partner.send_message(question['question'], reply_markup=[self.COMMANDS])

    def _get_not_asked_question(self, partner_id):
        asked_question_ids = {int(x) for x in self.redis.smembers(self.ASKED.format(partner_id))}
        not_asked = self.questions_ids_set - asked_question_ids
        if not not_asked:
            self.redis.delete(self.ASKED.format(partner_id))
            not_asked = self.questions_ids_set
        question_id = random.choice(list(not_asked))
        self.redis.sadd(self.ASKED.format(partner_id), question_id)
        return self.questions[question_id]
