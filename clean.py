from common import log_call, debug_group
from telegram_util import log_on_fail, matchKey, isCN
from dbase import channels, timestamp, index, maintext, suspect
import dbase
import time
import unicodedata
import webgram

def getScore(key):
	c_score = channels.get(key.split('/')[0])
	score = timestamp.get(key, 0) - c_score * 1000
	if c_score == -2:
		return 1
	if c_score == -1:
		return 0
	return -score

@log_call()
def save():
	index.save_dont_call_in_prod()
	maintext.save_dont_call_in_prod()
	timestamp.save_dont_call_in_prod()
	channels.save_dont_call_in_prod()

def createBucket(items):
	bucket = {}
	for key, text in items:
		if text in bucket:
			bucket[text].append(key)
		else:
			bucket[text] = [key]
	return bucket

def cleanKeys(keys, limit):
	count = 0 
	key_score = [(getScore(key), key) for key in keys]
	key_score.sort()
	for score, key in key_score[limit:]:
		dbase.removeKey(key)
		count += 1
	return count

@log_call()
def cleanupRedundant():
	items = [(item[0], item[1][:10]) for item in maintext.items()]
	items = [item for item in items if not item[0].endswith('/0')]
	bucket = createBucket(items)
	print('cleanupRedundant bucket size', len(bucket.items()))
	count = 0
	for text, keys in bucket.items():
		count += cleanKeys(keys, 1)
	print('cleanupRedundant removed %d items' % count)

def containCN(text):
	if not text:
		return False
	for c in text:
		if isCN(c):
			return True
	return False

def noCNnoEN(text):
	if not text:
		return True
	if containCN(text):
		return False
	for c in text:
		try:
			if matchKey(unicodedata.name(c), ['arabic', 'cyrillic']):
				return True
		except:
			...
	return False

def shouldRemove(key):
	if key.endswith('/0'):
		return False
	if not maintext.get(key):
		return True
	channel = key.split('/')[0]
	if channels.get(channel) == -2:
		return True
	if 0 <= channels.get(channel) < 2:
		return False
	if noCNnoEN(index.get(key)):
		return True
	if matchKey(index.get(key), ['hasFile', 'hasLink']):
		return False
	if timestamp.get(key, 0) < dbase.getRetain(key.split('/')[0]):
		return True
	return False

def getRetainLen(channel):
	score = channels.get(channel)
	if score < 0:
		return 30
	return int(300 + 6000 / (1 + score))

def cleanupOldOrBad(keys):
	keys.sort()
	keys = keys[1:-1] # leave the last one
	count = 0
	rest = []
	for key in keys:
		if shouldRemove(key):
			dbase.removeKey(key)
			count += 1
		else:
			rest.append(key)
	if len(rest) < 300:
		return count
	retain_len = getRetainLen(rest[0].split('/')[0])
	for key in rest[:-retain_len]:
		dbase.removeKey(key)
		count += 1
	return count

def cleanupChannel(keys):
	if not keys:
		return 0
	keys = [key for key in keys if not containCN(index.get(key))]
	return cleanKeys(keys, 10)

@log_call()
def cleanupSuspectAndOld():
	items = [(item[0], item[0].split('/')[0]) for item in maintext.items()]
	items = [item for item in items if not item[0].endswith('/0')]
	bucket = createBucket(items)
	count = 0
	for channel in bucket:
		if channels.get(channel) == -2:
			count += cleanKeys(bucket[channel], 0)
		if channels.get(channel) <= -1:
			count += cleanupChannel(bucket[channel])
		count += cleanupOldOrBad(bucket[channel])
	for channel in suspect.items():
		if channels.get(channel) >= 3:
			count += cleanupChannel(bucket.get(channel))
	print('cleanupSuspect removed %d items' % count)

@log_call()
def removeNonExistChannel():
	channel_to_remove = set()
	for key, title in maintext.items():
		if not key.endswith('/0'):
			continue
		if not title:
			channel_to_remove.add(key.split('/')[0])
	items = [(item[0], item[0].split('/')[0].lower()) for item in maintext.items()]
	bucket = createBucket(items)
	for channel_lower in bucket:
		items = bucket[channel_lower]
		items = [(item, item.split('/')[0]) for item in items]
		sub_bucket = createBucket(items)
		sub_bucket = [(len(item[1]), item[0]) for item in sub_bucket.items()]
		sub_bucket.sort(reverse=True)
		for _, channel in sub_bucket[1:]:
			channel_to_remove.add(channel)
	print('remove channel count', len(channel_to_remove))
	count = 0
	for key, _ in maintext.items():
		if key.split('/')[0] in channel_to_remove:
			dbase.removeKey(key)
			count += 1
	print('remove non exist', count)
	for channel in channel_to_remove:
		channels._db.items.pop(channel, None)

@log_on_fail(debug_group)
@log_call()
def indexClean():
	removeNonExistChannel()
	save()
	cleanupSuspectAndOld()
	save()
	cleanupRedundant()
	save()	