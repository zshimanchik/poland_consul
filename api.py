import json


class Partner:
    def __init__(self, id):
        self.id = id
        self.messages = []

    def send_message(self, text, reply_markup=None):
        if reply_markup:
            text += " " + json.dumps(reply_markup, ensure_ascii=False)
        self.messages.append(text)

    def read_message(self):
        if self.messages:
            return self.messages.pop(0)

    def read_messages(self):
        res = self.messages.copy()
        self.messages.clear()
        return res
