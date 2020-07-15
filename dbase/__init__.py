import plain_db
import webgram
from telegram_util import matchKey, log_on_fail
from common import isSimplified, log_call, debug_group

blocklist = plain_db.loadKeyOnlyDB('blocklist')
channels = plain_db.loadLargeDB('channels', isIntValue = True, default = 100)
index = plain_db.loadLargeDB('index')
maintext = plain_db.loadLargeDB('maintext')
timestamp = plain_db.loadLargeDB('timestamp', isIntValue = True)
channelrefer = plain_db.loadKeyOnlyDB('channelrefer')

def setBadWord(text):
	blocklist.add(text)

def setChannelScore(text):
	score = int(text.split()[-1])
	text = text.split()[0].strip('/').split('/')[-1]
	channels.update(text, score)

def updateChannel(name, referer):
	referer_score = channels.get(referer)
	if (referer_score < 0 or 
		channels.get(name) < referer_score + 1):
		return
	channels.update(name, referer_score + 1)
	channelrefer.add(name + ':' + referer)

def getIndexMaxLen(channel):
	score = channels.get(channel)
	if score == -2:
		return 0
	if score == -1:
		score = 100
	return int(2000 / (score + 1) ** 0.5)

def updateIndex(key, text, channel):
	text = text[:getIndexMaxLen(channel)]
	if not text:
		index.update(key, text) # post deleted
		return
	if not index.get(key):
		index.update(key, text)
		return
	for keyword in ['hasFile', 'hasLink']:
		if keyword in text and keyword not in index.get(key):
			index.update(key, text)
			return

def updateMaintext(key, text):
	if maintext.get(key):
		return
	maintext.update(key, text)

def updateTime(key, time):
	if timestamp.get(key) and time - timestamp.get(
		key) < 60 * 60 * 24 * 7:
		return
	timestamp.update(key, time)

def update(post):
	for channel in webgram.yieldReferers(post):
		updateChannel(channel, post.channel)
	updateIndex(post.getKey(), post.getIndex(), post.channel)
	updateMaintext(post.getKey(), post.getMaintext())
	updateTime(post.getKey(), post.time)

def suspectBadChannel(post):
	channel = post.channel
	total_count = 0
	bad_count = 0
	for item in channelrefer.items():
		from_channel, to_channel = item.split(':')
		if from_channel == channel:
			total_count += 1
			if channels.get(to_channel) == -2:
				bad_count += 1
	if bad_count * 5 > total_count:
		return True
	return matchKey(post.getIndex(), blocklist.items())