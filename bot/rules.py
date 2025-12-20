import datetime

def rule_current_time(user_input):
    if "!время" in user_input.lower():
        return "Текущее время: " + datetime.datetime.now().strftime("%H:%M:%S")

def rule_bot_mention(user_input):
    if "бот" in user_input.lower():
        return "Я тут. Че хотел?"
        
def rule_halo(user_input):
    if "halo" in user_input.lower():
        return "Старая добрая тройка... Вот это был кооп."

def rule_тема_бот(user_input):
    if "бот" in user_input.lower():
        return "Да, я бот. Но зато не туплю как те в Firefight."