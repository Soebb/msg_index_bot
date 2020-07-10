from bs4 import BeautifulSoup
import cached_url
from telegram_util import isCN, commitRepo
import random
import hanzidentifier
from channel import Channel

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
	addMentionedChannelWithCallback(item)

def shouldProcessFullBackfill(channel, score):
	if score > 1:
		return False
	if random.random() > 0.1:
		return False
	if score == 1 and random.random() > 0.1:
		return False
	return True

def getButtonText(soup):
	item = soup.find('a', class_='tgme_action_button_new')
	return (item and item.text) or ''

def isMostCN(text):
	if not text or not text.strip():
		return False
	cn = sum([isCN(c) + hanzidentifier.is_simplified(c) for c in text])
	for c in text:
		if isCN(c) and not hanzidentifier.is_simplified(c):
			return False
	return cn * 2 >= len(text)

def isGoodChannel(channel, db):
	if random.random() > 0.06:
		return False
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
	addMentionedChannelWithCallback(description, 
		lambda name, referer: Channel(name, referer).save(db))
	description = (description and description.text) or ''
	if isMostCN(title):
		print(title, description, isMostCN(description), 
			db.badScore(title), db.badScore(description))
	if db.badScore(title) or db.badScore(description):
		return False
	return isMostCN(title) and isMostCN(description)

def getItem(channel, index, callback):
	prefix = 'https://t.me/%s/' % channel
	link = prefix + str(index) + '?embed=1'
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	if (not soup.find('div', class_='tgme_widget_message_text') and 
		not soup.find('div', class_='tgme_widget_message_document_title')):
		return
	item = soup.find('div', class_='tgme_widget_message_bubble')
	if item:
		callback(item)
	return item

def findLastMessage(channel, callback):
	left = 1
	right = 100000
	while left < right - 100:
		item = None
		for _ in range(5):
			index = int(left + (random.random() * 0.5 + 0.25) * (right - left))
			item = getItem(channel, index, callback)
			if item:
				break
		if item:
			left = index
		else:
			right = int((left + 3 * right) / 4)
	return left

def backfillChannelNew(channel, callback, db, total = 500):
	max_index = findLastMessage(channel, callback)
	print('backfillChannelNew findIndex', channel, max_index)
	existing_index = set([None])
	new_index = set()
	post = max(1, max_index - total)
	while post < max_index:
		post_link = channel + '/' + str(post)
		existing_index.add(db.index.items.get(post_link))
		if not getItem(channel, post, callback):
			db.remove(post_link)
		new_item = db.index.items.get(post_link)
		if new_item not in existing_index:
			new_index.add(new_item)
		if post % 100 == 0:
			print('jumpinfo', channel, len(existing_index), len(new_index))
		if len(new_index) == 0 and len(existing_index) > 5:
			print('jump', channel)
			post += 100
			existing_index = set()
		post += 1
	db.save()
	commitRepo(delay_minute=0)