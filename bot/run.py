import json
from bot import GSK_Bot
from rules import rule_current_time, rule_bot_mention

# Загружаем пары диалога
with open("dialog_pairs.jsonl", "r", encoding="utf-8") as f:
    dialogue_pairs = [json.loads(line) for line in f]

# Инициализируем бота
bot = GSK_Bot([(pair["prompt"], pair["response"]) for pair in dialogue_pairs])
bot.add_rule(rule_current_time)
bot.add_rule(rule_bot_mention)

print("Бот ChatGSK enable. Напиши 'стоп' чтобы выйти.")

while True:
    user_input = input("Ты: ")
    if user_input.lower() in ["стоп", "exit", "выход"]:
        print("Бот: Бывай.")
        break
    print("Бот:", bot.get_reply(user_input))
