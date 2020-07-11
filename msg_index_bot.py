#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import MessageHandler, Filters
from db import DB
from channel import Channel
from telegram_util import log_on_fail, cutCaption, commitRepo, splitCommand, removeOldFiles
import threading
from bs4 import BeautifulSoup
import cached_url
from datetime import datetime
import random
from helper import isGoodChannel, backfillChannelNew, shouldProcessFullBackfill, tryAddAllMentionedChannel, isMostCN
from debug import debug_group, tele, sendDebugMessage, log_call
from db import db

HELP_MESSAGE = '''
添加频道，群组 - "/add @dushufenxiang", 可批量。
搜索频道 - "/search_channel 读书", "/sc 读书"
搜索消息 - 直接输入"李星星", 或 "/search 李星星", "/s 李星星"
'''

def findChannels(text):
	result = []
	for x in text.split():
		if not x:
			continue
		if x.startswith('@'):
			result.append(Channel(x[1:]))
			continue
		if 't.me' in x:
			result.append(Channel(x.strip('/').split('/')[-1]))
			continue
	result = [x for x in result if x.exist()]
	[x.save(db, None) for x in result]
	return result

def search(msg, text, method):
	if len(text.split()) != 1:
		return
	tmp = msg.reply_text('searching')
	result = method(text)
	msg.forward(debug_group.id)
	if result:
		r = msg.reply_text('\n'.join(result), disable_web_page_preview = True, parse_mode = 'Markdown')
	else:
		r = msg.reply_text('no result')	
	r.forward(debug_group.id)
	tmp.delete()

@log_on_fail(debug_group)
def handleCommand(update, context):
	msg = update.message # Do not support command in channel
	command, text = splitCommand(msg.text)
	if 'add' in command:
		findChannels(text)
		msg.reply_text('success')
		return
	if 'channel' in command or command == '/sc':
		search(msg, text, db.searchChannel)
		return
	if 'start' in command:
		msg.reply_text(HELP_MESSAGE, disable_web_page_preview=True)
		return
	if 'search' in command or command == '/s':
		search(msg, text, db.search)
		return
	if msg.from_user and msg.from_user.id == debug_group.id:
		if command == '/sb':
			msg.reply_text(db.setBadness(text))
			return
		if command in ['/vb']:
			msg.reply_text(db.getBadness(text))
			return
	if msg.chat_id > 0:
		msg.reply_text(HELP_MESSAGE, disable_web_page_preview=True)
		return

def tryAddChannelBubble(name, referer):
	try:
		Channel(name).save(db, referer)
	except Exception as e:
		...

def tryAddChannel(chat, referer = None):
	try:
		tryAddChannelBubble(chat.username, referer and referer.username)
	except Exception as e:
		...

def getPostLink(msg):
	try:
		return '%s/%s' % (msg.forward_from_chat.username, msg.forward_from_message_id)
	except:
		if not msg.chat.username:
			return
		return '%s/%s' % (msg.chat.username, msg.message_id)

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
	db.setMainText(post_link, getCompact(text))
	db.setTime(post_link, int(msg.date.timestamp()))

@log_on_fail(debug_group)
def backfillBotChannel(channel):
	main_msg = tele.bot.send_message(channel, 'test')
	main_msg.delete()
	for mid in range(2200, 2500): # main_msg.message_id
		try:
			msg = tele.bot.forward_message(debug_group.id,
				main_msg.chat_id, mid)
			msg.delete()
		except:
			continue
		if mid % 100 == 0:
			sendDebugMessage('backfillBotChannel1 ' + str(mid))
			db.save()
			commitRepo(delay_minute=0)
			sendDebugMessage('backfillBotChannel2 ' + str(mid))
		indexFromTelegramMsg(msg)
	db.save()
	commitRepo(delay_minute=0)

@log_on_fail(debug_group)
def handleGroup(update, context):
	msg = update.effective_message
	if db.isBadMsg(msg):
		return
	indexFromTelegramMsg(msg)


@log_on_fail(debug_group)
def handleSearch(update, context):
	msg = update.message
	text = msg.text.strip()
	search(msg, text, db.search)

def getPostLinkBubble(item):
	try:
		result = item.find('a', class_='tgme_widget_message_forwarded_from_name')['href']
		int(result.strip('/').split('/')[-1])
		return result
	except:
		return item.find('a', class_='tgme_widget_message_date')['href']

def getOrigChannel(item):
	orig_link = item.find('a', class_='tgme_widget_message_date')['href']
	return orig_link.strip('/').split('/')[-2]

def getText(item, class_name):
	try:
		return item.find('div', class_=class_name).text
	except:
		return ''

def getCompact(text, cut = 20):
	if not text:
		return ''
	for char in '[]()':
		text = text.replace(char, '') 
	return cutCaption(' '.join(text.split()).strip(), '', cut)

def getMainText(text_fields):
	if text_fields[0] and len(text_fields[0]) > 5:
		return text_fields[0]
	for x in text_fields[1:] + [text_fields[0]]:
		if x:
			return x

def getTime(item):
	try:
		s = (item.find('a', class_='tgme_widget_message_date').
				find('time')['datetime'][:-6])
	except:
		print(item.find('a', class_='tgme_widget_message_date'))
		return 0
	format = '%Y-%m-%dT%H:%M:%S'
	return datetime.strptime(s, format).timestamp()

def processBubble(item):
	if db.isBadBubble(item):
		return
	post_link = getPostLinkBubble(item)
	tryAddChannelBubble(post_link.strip('/').split('/')[-2], getOrigChannel(item))
	tryAddAllMentionedChannel(item, tryAddChannelBubble)
	text_fields_name = [
		'link_preview_title',
		'tgme_widget_message_text', 
		'tgme_widget_message_document_title', 
		'link_preview_description']
	text_fields = [getText(item, field) for field in text_fields_name]
	if ''.join(text_fields) == '':
		return
	[db.addIndex(post_link, text) for text in text_fields]
	db.setMainText(post_link, getCompact(getMainText(text_fields)))
	db.setTime(post_link, getTime(item))

def getChannelTitle(soup):
	try:
		return getCompact(soup.find(
			'div', class_='tgme_channel_info_header_title').text, 10)
	except:
		...

@log_on_fail(debug_group)
def indexingImp():
	sendDebugMessage('start indexingImp')
	for channel in list(db.getChannels()):
		score = db.channels.items.get(channel, 100)
		if random.random() > 1.0 / (score * score + 1):
			continue
		link = 'https://t.me/s/%s' % channel
		soup = BeautifulSoup(cached_url.get(link), 'html.parser')
		if db.isBadChannel(soup):
			continue
		db.saveChannelTitle(channel, getChannelTitle(soup))
		for item in soup.find_all('div', class_='tgme_widget_message_bubble'):
			processBubble(item)
	db.save()
	commitRepo(delay_minute=0)
	sendDebugMessage('end indexingImp')

def backfillChannel(channel):
	start = 1
	prefix = 'https://t.me/s/%s/' % channel
	while True:
		original_start = start
		link = prefix + str(start)
		soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
		for item in soup.find_all('div', class_='tgme_widget_message_bubble'):
			processBubble(item)
			post_link = item.find('a', class_='tgme_widget_message_date')['href']
			post_id = int(post_link.split('/')[-1])
			start = max(start, post_id + 1)
		if start == original_start:
			return
	db.save()
	commitRepo(delay_minute=0)

def hasLink(item):
	if item.find('div', class_='tgme_widget_message_document_title'):
		return True
	text = item.find('div', class_='tgme_widget_message_text')
	if not text:
		return False
	return text.find('a')

def hasFile(item):
	return item.find('div', class_='tgme_widget_message_document_title')

def processBubbleWithLink(item):
	if hasLink(item):
		processBubble(item)

def processBubbleWithFile(item):
	if hasFile(item):
		processBubble(item)

@log_on_fail(debug_group)
def onlyFileBackfill(channel):
	print('onlyFileBackfill', channel)
	backfillChannelNew(channel, processBubbleWithFile, db, total = 1000000)

@log_on_fail(debug_group)
def backfill():
	removeOldFiles('tmp', day = 20)
	count = 0
	sendDebugMessage('backfill')
	for channel, score in list(db.channels.items.items()):
		count += 1
		if count % 1000 == 0:
			sendDebugMessage('backfill ' + str(count))
		if shouldProcessFullBackfill(channel, score):
			sendDebugMessage('process full backfill ' + channel)
			backfillChannelNew(channel, processBubble, db, total = 100000)
		if not db.isBadFromReferRelate(channel) and isGoodChannel(channel, db):
			sendDebugMessage('process partial backfill ' + channel)
			backfillChannelNew(channel, processBubbleWithLink, db)
	sendDebugMessage('backfill finish')

@log_on_fail(debug_group)
def purgeOldIndex():
	db.purgeOldIndex()
	db.save()
	commitRepo(delay_minute=0)

@log_on_fail(debug_group)
def trimIndex():
	sendDebugMessage('start triming index')
	db.trimIndex()
	sendDebugMessage('triming index 1')
	db.save()
	sendDebugMessage('triming index 2')
	commitRepo(delay_minute=0)
	sendDebugMessage('end triming index')

bad_channel = set()

@log_on_fail(debug_group)
def findBadChannel():
	for channel, score in list(db.channels.items.items()):
		if (db.badScore(channel + '/') == 0 and
				db.isBadFromReferRelate(channel) and 
				channel not in bad_channel):
			debug_group.send_message('isBadFromReferRelate: ' + 
				channel + str(list(db.getBadReferer(channel))))
		bad_channel.add(channel)

@log_call()
def indexing():
	db.dedupIndex()
	db.purgeDeletedChannel()
	# onlyFileBackfill('what_youread')
	indexingImp()
	findBadChannel()
	purgeOldIndex()
	backfill()
	threading.Timer(60, indexing).start()

if __name__ == '__main__':
	sendDebugMessage('restart')
	dp = tele.dispatcher
	threading.Timer(1, indexing).start() 
	dp.add_handler(MessageHandler(Filters.command, handleCommand))
	dp.add_handler(MessageHandler(~Filters.command & Filters.private, handleSearch))
	dp.add_handler(MessageHandler(~Filters.command & ~Filters.private, handleGroup))
	tele.start_polling()
	tele.idle()
