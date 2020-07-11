from telegram_util import cutCaption

def getCompact(text, cut = 20):
	if not text:
		return ''
	for char in '[]()\\':
		text = text.replace(char, '') 
	return cutCaption(' '.join(text.split()).strip(), '', cut)