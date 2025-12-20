import random

class GSK_Bot:
    def __init__(self, dialogue_pairs):
        self.dialogue = dialogue_pairs
        self.rules = []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def get_reply(self, user_input):
        for rule in self.rules:
            response = rule(user_input)
            if response:
                return response
        return self.match_from_dialogue(user_input)

    def match_from_dialogue(self, user_input):
        for q, a in reversed(self.dialogue):
            if user_input.lower() in q.lower():
                return a
        return "Без понятия, бро."

    def update_pairs(self, new_pairs):
        self.dialogue = new_pairs


class SPT_Bot:
    def __init__(self, dialogue_pairs):
        self.dialogue = dialogue_pairs
        self.rules = []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def get_reply(self, user_input):
        for rule in self.rules:
            response = rule(user_input)
            if response:
                return response
        return self.match_from_dialogue(user_input)

    def match_from_dialogue(self, user_input):
        for q, a in reversed(self.dialogue):
            if user_input.lower() in q.lower():
                return a
        return "Нужно просто попробовать."

    def update_pairs(self, new_pairs):
        self.dialogue = new_pairs


class VLM_Bot:
    def __init__(self, dialogue_pairs):
        self.dialogue = dialogue_pairs
        self.rules = []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def get_reply(self, user_input):
        for rule in self.rules:
            response = rule(user_input)
            if response:
                return response
        return self.match_from_dialogue(user_input)

    def match_from_dialogue(self, user_input):
        for q, a in reversed(self.dialogue):
            if user_input.lower() in q.lower():
                return a
        return "Смурь."

    def update_pairs(self, new_pairs):
        self.dialogue = new_pairs


class CST_Bot:
    def __init__(self, dialogue_pairs):
        self.dialogue = dialogue_pairs
        self.rules = []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def get_reply(self, user_input):
        for rule in self.rules:
            response = rule(user_input)
            if response:
                return response
        return self.match_from_dialogue(user_input)

    def match_from_dialogue(self, user_input):
        for q, a in reversed(self.dialogue):
            if user_input.lower() in q.lower():
                return a
        return "Настроить, настроить, настроить."

    def update_pairs(self, new_pairs):
        self.dialogue = new_pairs
