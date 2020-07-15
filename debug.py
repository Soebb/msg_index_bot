from telegram.ext import Updater

with open('token') as f:
	token = f.read().strip()
tele = Updater(token, use_context=True) # @msg_index_bot
debug_group = tele.bot.get_chat(420074357)

last_debug_message = None

def sendDebugMessage(*args):
	message = ' '.join([str(x) for x in args])
	global last_debug_message
	if last_debug_message:
		last_debug_message.delete()
	last_debug_message = debug_group.send_message(message)

def log_call():
	def decorate(f):
		def applicator(*args, **kwargs):
			print(f.__name__, str(args), 'start')
			new_args = [f.__name__] + args + ['start']
			sendDebugMessage(*new_args)
			f(*args,**kwargs)
			new_args[-1] = 'end'
			sendDebugMessage(*new_args)
			print(f.__name__, str(args), 'end')
		return applicator
	return decorate