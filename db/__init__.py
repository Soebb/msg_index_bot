from .dbitem import DBItem
import yaml
import time
from debug import sendDebugMessage, debug_group, log_call
from telegram_util import log_on_fail
from channel import Channel

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
		self.channelname = DBItem('channelname', random_save = True)
		self.channelrefer = DBItem('channelrefer', value_int = True, random_save = True)
		
	def finalTouch(self, result):
		final_result = result[:20]
		final_result = ['%d. [%s](https://t.me/%s)' % (index + 1, x[0], x[1]) 
			for index, x in enumerate(final_result)]
		return final_result

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

	def isBadBubble(self, soup):
		return False

	def save(self):
		self.channels.save()
		self.index.save()
		self.maintext.save()
		self.time.save()
		self.channelname.save()
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

	def getChannels(self):
		return self.channels.items.keys()

	def addChannel(self, key, referer=None):
		if referer == key:
			referer = None
		rank = self.channels.items.get(key, 100)
		rank = min(rank, self.channels.items.get(referer, 100) + 1)
		self.channels.update(key, rank)
		self.channelrefer.inc(str(referer) + ':' + key)

	def saveChannelTitle(self, key, title):
		if not title:
			return
		self.channelname.update(key, title)

	def searchRaw(self, text):
		for key, value in list(self.index.items.items()):
			if text.lower() in value.lower():
				yield key

	def searchChannel(self, text):
		hit_count = {}
		total_count = {}
		posts = {}
		for key, value in list(self.index.items.items()):
			channel = key.split('/')[0]
			if text.lower() in value.lower():
				hit_count[channel] = hit_count.get(channel, 0) + 1 
				if text.lower() in self.maintext.items.get(key, '').lower():
					posts[channel] = key
				if channel not in posts:
					posts[channel] = key
			total_count[channel] = total_count.get(channel, 0) + 1 
		raw_result = [(hit_count[key] * 1.0 / total_count[key], key) 
			for key in hit_count]
		raw_result.sort(reverse=True)
		result = []
		for _, channel in raw_result:
			name = self.channelname.items.get(channel)
			if not name:
				continue
			result.append((name, posts[channel]))
		result = ([x for x in result if text.lower() in x[0].lower()] + 
			[x for x in result if text.lower() not in x[0].lower()])
		return self.finalTouch(result)

	def search(self, text):
		result = list(self.searchRaw(text))
		result = [(self.time.items.get(x, 0), x) for x in result]
		result.sort(reverse=True)
		
		exist_maintext = set()
		exist_channel = set()
		first = []
		rest = []
		resttop = []
		for _, x in result:
			main_text = self.maintext.items.get(x)
			channel = x.split('/')[0]
			if not main_text or main_text in exist_maintext:
				continue
			exist_maintext.add(main_text)
			item = (main_text, x)
			if self.badScore(item) >= 20:
				continue
			if (self.badScore(item) > 0 and 
				self.channels.items.get(channel, 100) > 0):
				rest.append(item)
			elif channel in exist_channel:
				resttop.append(item)
			else:
				first.append(item)
			exist_channel.add(channel)

		result = ([x for x in first if text.lower() in x[0].lower()] + 
			[x for x in first if text.lower() not in x[0].lower()] + 
			resttop + rest)
		return self.finalTouch(result)

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

	def trimIndex(self):
		for key, value in list(self.index.items.items()):
			self.index.update(key, trimIndexItem(value))

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
		self.channelname.remove(channel)
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