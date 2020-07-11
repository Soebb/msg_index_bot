from .dbitem import DBItem
import yaml
import time
from debug import sendDebugMessage, debug_group, log_call
from telegram_util import log_on_fail
from channel import Channel
from search import searchText, searchChannel

sign = '。，？！.,\n'

def addToResult(result, buff):
	buff = ''.join(buff).strip().split()
	for b in buff:
		flag = False
		for x in result:
			if b in x:
				flag = True
		if not flag:
			result.append(b)

def stripPostLink(link):
	return link.strip().strip('/').split('https://t.me/')[-1]

def trimIndexItem(value):
	parts = list(set(value.split()))
	parts.sort()
	return ' '.join(parts).strip()

class DB(object):
	def __init__(self):
		self.blacklist = DBItem('blacklist', value_int = True)
		self.channels = DBItem('channels', value_int = True)
		self.index = DBItem('index', random_save = True)
		self.maintext = DBItem('maintext', random_save = True)
		self.time = DBItem('time', value_int = True, random_save = True)
		self.channelrefer = DBItem('channelrefer', value_int = True, random_save = True)
		# deprecated
		self.channelname = DBItem('channelname', random_save = True) 
		
	def badScore(self, text):
		score = 0
		if not text:
			return 0
		text = str(text).lower()
		r = []
		for key, value in self.blacklist.items.items():
			if key.lower() in text:
				score += value
				r.append(key)
		return score

	def isBadMsg(self, msg):
		return self.badScore(msg.chat.username) >= 20

	def isBadChannel(self, soup):
		channel_username = ''
		try:
			channel_username = soup.find('div', class_='tgme_channel_info_header_username').text
		except:
			pass
		return self.badScore(channel_username) >= 20

	def save(self):
		self.channels.save()
		self.index.save()
		self.maintext.save()
		self.time.save()
		self.channelrefer.save()

	def addIndex(self, post_link, text):
		text = text and text.strip()
		if not text:
			return
		post_link = stripPostLink(post_link)
		result = [self.index.items.get(post_link, '')]
		buff = []
		for char in text:
			if char in sign:
				addToResult(result, buff)
				buff = []
				continue
			buff.append(char)
		addToResult(result, buff)
		result = trimIndexItem(' '.join(result))
		if not result:
			return
		self.index.update(post_link, result)

	def setMainText(self, post_link, text):
		post_link = stripPostLink(post_link)
		self.maintext.update(post_link, text)

	def setTime(self, post_link, time):
		post_link = stripPostLink(post_link)
		self.time.updateIfLarger(post_link, int(time))

	def addChannel(self, key, referer=None):
		if referer == key:
			referer = None
		rank = self.channels.items.get(key, 100)
		rank = min(rank, self.channels.items.get(referer, 100) + 1)
		self.channels.update(key, rank)
		self.channelrefer.inc(str(referer) + ':' + key)

	def isBadFromReferRelate(self, channel):
		if self.badScore(channel + '/') >= 20:
			return True
		badness = 0
		total = 0
		for refer, count in self.channelrefer.items.items():
			if refer.startswith(channel):
				badness += count * self.badScore(refer)
				total += count
		return badness * 1.0 / (total + 0.1) > 9

	def getBadReferer(self, channel):
		badness = 0
		for refer, count in self.channelrefer.items.items():
			if refer.startswith(channel) and self.badScore(refer) > 9:
				yield refer

	def remove(self, key):
		self.index.remove(key)
		self.maintext.remove(key)
		self.time.remove(key)

	def setBadness(self, text):
		key, value = text.split()
		value = int(value)
		self.blacklist.update(key, value)
		return 'success'

	def getBadness(self, text):
		return str(self.blacklist.items.get(text, 0))

	@log_on_fail(debug_group)
	def _purgeChannel(self, channel):
		for key, value in self.index.getItems():
			if channel == key.split('/')[0]:
				self.remove(key)
		self.channels.remove(channel)
		self.save()

	@log_on_fail(debug_group)
	@log_call()
	def purgeChannels(self):
		for channel, _ in self.channels.getItems():
			if (self.isBadFromReferRelate(channel) or
				not Channel(channel).exist()):
				db._purgeChannel(channel)

	@log_on_fail(debug_group)
	@log_call()
	def dedupIndex(self):
		tmp_set = set()
		for key, value in self.index.getItems():
			if value not in tmp_set:
				tmp_set.add(value)
			else:
				self.remove(key)
		for key, value in list(self.maintext.getItems()):
			if not self.index.items.get(key):
				self.remove(key)
		self.save()

db = DB()