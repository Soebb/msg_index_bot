from db import db
from telegram_util import cutCaption
from channel import Channel

def getCompact(text, cut = 20):
	if not text:
		return ''
	for char in '[]()\\':
		text = text.replace(char, '') 
	return cutCaption(' '.join(text.split()).strip(), '', cut)

def addChannelRaw(raw, referer):
	raw = raw[raw.find('/t.me/'):].strip('/').split('/')
	if len(raw) >= 2: 
		Channel(raw[1]).save(db, referer)