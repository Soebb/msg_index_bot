import plain_db
from telegram_util import removeOldFiles
import dbase
from dbase import index, maintext, timestamp, channels, suspect
from common import log_call
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
	for text, keys in bucket.items():
		key_score = [(getScore(key), key) for key in keys]
		key_score.sort()
		for score, key in key_score[1:]:
			dbase.removeKey(key)
		if key_score[0][0] == 102:
			dbase.removeKey(key_score[0][1])

@log_call()
def cleanupNoMain():
	count = 0
	for key, text in index.items():
		if not maintext.get(key):
			count += 1
			dbase.removeKey(key)
	print('cleanupNoMain', count)

def cleanupChannel(keys):
	sort_keys = [(getKeyScore(key), key) for key in keys]
	sort_keys.sorted(reverse=True)
	for key in sort_keys[100:]:
		dbase.removeKey(key)

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
	for channel in bucket:
		if channels.get(channel) <= -1:
			cleanupChannel(bucket[channel])
	for channel in suspect:
		if channels.get(channel) > 5:
			cleanupChannel(bucket[channel])

@log_call()
def save():
	index.save_dont_call_in_prod()
	maintext.save_dont_call_in_prod()
	timestamp.save_dont_call_in_prod()
	channels.save_dont_call_in_prod()
	removeOldFiles('tmp', day = 1)

if __name__ == '__main__':
	cleanupRedundant()
	save()
	cleanupNoMain()
	save()
	cleanupSuspect()
	save()
