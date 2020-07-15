from telegram.ext import Updater

with open('token') as f:
	token = f.read().strip()
tele = Updater(token, use_context=True)  # @weibo_subscription_bot
debug_group = tele.bot.get_chat(420074357)