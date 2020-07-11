from bs4 import BeautifulSoup
import cached_url
from telegram_util import isCN, commitRepo
import random
import hanzidentifier
from channel import Channel
from common import getButtonText
import time

def addMentionedChannelWithCallback(item, callback):
	if not item:
		return
	for link in item.find_all('a'):
		link = link.get('href', '')
		if link.find('/t.me/') == -1:
			continue
		callback(link.strip('/').split('/')[-1], '')

def tryAddAllMentionedChannel(item, callback):
	item = item.find('div', class_='tgme_widget_message_text')
	if not item:
		return
	addMentionedChannelWithCallback(item, callback)

def shouldProcessFullBackfill(channel, score):
	if score > 1:
		return False
	if random.random() > 0.1:
		return False
	if score == 1 and random.random() > 0.1:
		return False
	return True

def isMostCN(text):
	if not text or not text.strip():
		return False
	cn = sum([isCN(c) + hanzidentifier.is_simplified(c) for c in text])
	for c in text:
		if isCN(c) and not hanzidentifier.is_simplified(c):
			return False
	return cn * 2 >= len(text)

def isGoodChannel(channel, db):
	# if random.random() > 0.06:
	# 	return False
	link = 'https://t.me/%s' % channel
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	title = soup.find('div', class_='tgme_page_title')
	if not title:
		return False
	title = title.text
	if 'Send Message' in getButtonText(soup):
		return False
	description = (soup.find('div', class_='tgme_channel_info_description') or
		soup.find('div', class_='tgme_page_description'))
	print('description', description)
	addMentionedChannelWithCallback(description, 
		lambda name, _: Channel(name).save(db, channel))
	description = (description and description.text) or ''
	if isMostCN(title):
		print(title, description, isMostCN(description), 
			db.badScore(title), db.badScore(description))
	if db.badScore(title) or db.badScore(description):
		return False
	return isMostCN(title) and isMostCN(description)


