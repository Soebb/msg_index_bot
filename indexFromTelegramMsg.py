from channel import Channel
from telegram_util import log_on_fail
from debug import debug_group
from common import addChannelRaw, getCompact

def tryAddChannel(chat, referer = None):
	try:
		Channel(chat.username).save(db, referer and referer.username)
	except Exception as e:
		...

def getPostLink(msg):
	try:
		return '%s/%s' % (msg.forward_from_chat.username, msg.forward_from_message_id)
	except:
		if not msg.chat.username:
			return
		return '%s/%s' % (msg.chat.username, msg.message_id)

def addChannel(raw, referer):
	if raw.startswith('@'):
		Channel(raw[1:].strip()).save(db, referer)	
		return
	addChannelRaw(raw, referer)

@log_on_fail(debug_group)
def indexFromTelegramMsg(msg):
	tryAddChannel(msg.chat, None)
	tryAddChannel(msg.forward_from_chat, msg.chat)
	post_link = getPostLink(msg)
	if not post_link:
		return
	text = msg.text or msg.caption or (
		msg.document and msg.document.file_name)
	db.addIndex(post_link, text)
	if msg.document:
		db.addIndex(post_link, 'hasFile')
	for entity in msg.entities or msg.caption_entities or []:
		if entity["type"] in ["url", "text_link"]:
			db.addIndex(post_link, 'hasLink')
		url = text[entity["offset"]:][:entity["length"]]
		addChannel(url, post_link.split('/')[-2])
	db.setMainText(post_link, getCompact(text))
	db.setTime(post_link, int(msg.date.timestamp()))