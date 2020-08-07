from common import log_call, debug_group
from telegram_util import log_on_fail, matchKey, isCN
from dbase import channels, timestamp, index, maintext, suspect
import dbase
import time

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

def shouldRemove(key):
	channel = key.split('/')[0]
	if channels.get(channel) == -2:
		return True
	if matchKey(index.get(key), ['hasFile', 'hasLink']):
		return False
	if 0 <= channels.get(channel) < 3:
		return False
	if timestamp.get(key) < time.time() - 365 * 60 * 60 * 24:
		return True
	return False

@log_call()
def cleanupKey():
	count = 0
	for key, text in maintext.items():
		if not text or shouldRemove(key):
			dbase.removeKey(key)
			count += 1
	print('cleanupKey removed %d items' % count)

def containCN(text):
	if not text:
		return False
	for c in text:
		if isCN(c):
			return True
	return False

def cleanupChannel(keys):
	keys = [key for key in keys is not containCN(index.get(key))]
	return cleanKeys(keys, 10)

@log_call()
def cleanupSuspect():
	items = [(item[0], item[0].split('/')[0]) for item in maintext.items()]
	items = [item for item in items if not item[0].endswith('/0')]
	bucket = createBucket(items)
	count = 0
	for channel in bucket:
		if channels.get(channel) <= -1:
			count += cleanupChannel(bucket[channel])
	for channel in suspect.items():
		if channels.get(channel) >= 3:
			count += cleanupChannel(bucket.get(channel))
	print('cleanupSuspect removed %d items' % count)

@log_on_fail(debug_group)
@log_call()
def indexClean():
	# testing
	# cleanupRedundant()
	# save()
	cleanupKey()
	save()
	cleanupSuspect()
	save()
	