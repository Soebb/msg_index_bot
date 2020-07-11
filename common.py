from telegram_util import cutCaption

def getButtonText(soup):
	item = soup.find('a', class_='tgme_action_button_new')
	return (item and item.text) or ''

def getCompact(text, cut = 20):
	if not text:
		return ''
	for char in '[]()\\':
		text = text.replace(char, '') 
	return cutCaption(' '.join(text.split()).strip(), '', cut)