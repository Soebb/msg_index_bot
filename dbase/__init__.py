import plain_db
import webgram
from telegram_util import matchKey, log_on_fail
from common import isSimplified, log_call, debug_group, sendDebugMessage
import time

blocklist = plain_db.loadKeyOnlyDB('blocklist')
channels = plain_db.loadLargeDB('channels', isIntValue = True, default = 100)
index = plain_db.loadLargeDB('index')
maintext = plain_db.loadLargeDB('maintext')
timestamp = plain_db.loadLargeDB('timestamp', isIntValue = True)
channelrefer = plain_db.loadKeyOnlyDB('channelrefer')
suspect = plain_db.loadKeyOnlyDB('suspect')

status = {}

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

def shouldUpdateIndex(key, text):
	if not text or not index.get(key):
		return True
	return index.get(key)[:100] != text[:100]

def updateIndex(key, text, channel):
	text = text[:getIndexMaxLen(channel)]
	if shouldUpdateIndex(key, text):
		if not index.get(key):
			status['added'] += 1
		index.update(key, text)

def updateMaintext(key, text):
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

def removeKey(key):
	index._db.items.pop(key, None)
	maintext._db.items.pop(key, None)
	timestamp._db.items.pop(key, None)

def suspectBadChannel(post):
	if matchKey(post.getIndex() + post.getKey(), blocklist.items()):
		return True
	total_count = 0
	bad_count = 0
	for item in channelrefer.items():
		from_channel, to_channel = item.split(':')
		if from_channel == post.channel:
			total_count += 1
			if channels.get(to_channel) == -2:
				bad_count += 1
	if bad_count * 5 > total_count:
		return True
	return False

def isCNGoodChannel(channel):
	post = webgram.get(channel)
	if not post.exist:
		return False
	update(post)
	if channels.get(channel) in [0, 1]:
		return True
	if channels.get(channel) in [-1, -2]:
		return False
	if not isSimplified(post.getIndex()):
		return False
	return not suspectBadChannel(post)

def resetStatus():
	result = [int((time.time() - status.get('time', 0)) / 60),
		'minutes', status.get('added', 0), 'new item']
	status['time'] = time.time()
	status['added'] = 0
	return result

resetStatus()

coreIndex = set()

def isCore(key):
	if not index.get(key) or not maintext.get(key):
		return False
	channel = key.split('/')[0]
	if not (0 <= channels.get(channel) <=5):
		return False
	if 0 <= channels.get(channel) <=1:
		return True
	return timestamp.get(key, 0) > time.time() - 7 * 60 * 60 * 24

@log_on_fail(debug_group)
@log_call()
def fillCoreIndex():
	sendDebugMessage(*['fillCoreIndex start', len(index.items())] + 
		resetStatus(), persistent=True)
	for key, _ in index.items():
		if isCore(key):
			coreIndex.add(key)
	sendDebugMessage(*['fillCoreIndex finish', len(coreIndex)] + 
		resetStatus(), persistent=True)