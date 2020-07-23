import plain_db
from telegram_util import removeOldFiles, matchKey
import dbase
from dbase import index, maintext, timestamp, channels, suspect
from common import log_call, isSimplified
import time

def getScore(key):
	raw = channels.get(key.split('/')[0])
	if raw == -2:
		return 102
	if raw == -1:
		return 101
	return raw

@log_call()
def cleanupRedundant():
	bucket = {}
	for key, text in maintext.items():
		text = text[:10]
		if text in bucket:
			bucket[text].append(key)
		else:
			bucket[text] = [key]
	print('cleanup1 1', len(bucket.items()))
	count = 0
	for text, keys in bucket.items():
		key_score = [(getScore(key), key) for key in keys]
		key_score.sort()
		for score, key in key_score[1:]:
			dbase.removeKey(key)
			count += 1
		if key_score[0][0] == 102:
			dbase.removeKey(key_score[0][1])
	print('cleanupRedundant', count)

@log_call()
def cleanupNoMain():
	count = 0
	for key, text in index.items():
		if not maintext.get(key):
			count += 1
			dbase.removeKey(key)
	print('cleanupNoMain', count)

def getKeyScore(key):
	if matchKey(index.get(key), ['hasFile', 'hasLink']):
		return 1
	return 0

def cleanupChannel(keys, keepChinese=True):
	if not keys or len(keys) <= 100:
		return 0 
	if keepChinese:
		result_keys = []
		for key in keys:
			if not isSimplified(index.get(key)):
				result_keys.append(key)
		keys = result_keys
	if len(keys) <= 50:
		return 0
	sort_keys = [(getKeyScore(key), key) for key in keys]
	sort_keys.sort(reverse=True)
	count = 0
	for key in sort_keys[50:]:
		dbase.removeKey(key[1])
		count += 1
	return count

@log_call()
def cleanupSuspect():
	bucket = {}
	for key, text in maintext.items():
		if key.endswith('/0'):
			continue
		text = key.split('/')[0]
		if text in bucket:
			bucket[text].append(key)
		else:
			bucket[text] = [key]
	count = 0
	for channel in bucket:
		if channels.get(channel) <= -1:
			count += cleanupChannel(bucket[channel], keepChinese=False)
	for channel in suspect.items():
		if channels.get(channel) > 5:
			count += cleanupChannel(bucket.get(channel))
	print('cleanupSuspect', count)

@log_call()
def save():
	start = time.time()
	index.save_dont_call_in_prod()
	maintext.save_dont_call_in_prod()
	timestamp.save_dont_call_in_prod()
	channels.save_dont_call_in_prod()
	# removeOldFiles('tmp', day = 2)

if __name__ == '__main__':
	cleanupRedundant()
	save()
	cleanupNoMain()
	save()
	cleanupSuspect()
	save()
