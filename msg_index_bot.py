#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import MessageHandler, Filters
from db import DB
from channel import Channel
from telegram_util import log_on_fail, cutCaption, splitCommand
import threading
from bs4 import BeautifulSoup
import cached_url
import random
from helper import isGoodChannel, backfillChannelNew, shouldProcessFullBackfill, tryAddAllMentionedChannel, isMostCN
from debug import debug_group, tele, sendDebugMessage, log_call
from db import db
from processIndex import processBubble, processChannelInfo
from common import getCompact

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

@log_on_fail(debug_group)
@log_call()
def indexingImp():
	for channel, score in db.channels.getItems():
		if random.random() > 1.0 / (score * score + 1):
			continue
		link = 'https://t.me/s/%s' % channel
		soup = BeautifulSoup(cached_url.get(link), 'html.parser')
		if db.isBadChannel(soup):
			continue
		processChannelInfo(channel, soup)
		for item in soup.find_all('div', class_='tgme_widget_message_bubble'):
			processBubble(item)
	db.save()

@log_on_fail(debug_group)
@log_call()
def backfill():
	for channel, score in db.channels.getItems():
		if shouldBackfill(channel, score):
			backfillChannel(channel)

bad_channel = set()
@log_on_fail(debug_group)
def findBadChannel():
	for channel, score in db.channels.getItems():
		if (db.badScore(channel + '/') == 0 and
				db.isBadFromReferRelate(channel) and 
				channel not in bad_channel):
			debug_group.send_message('isBadFromReferRelate: ' + 
				channel + str(list(db.getBadReferer(channel))))
		bad_channel.add(channel)

@log_call()
def indexing():
	indexingImp()
	findBadChannel()
	db.purgeChannels()
	db.dedupIndex()
	# onlyFileBackfill('what_youread')
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
