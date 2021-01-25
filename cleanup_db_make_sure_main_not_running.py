# may need to remove all posts with 

# 1) no chinese in description (any form of chinese)
# 2) no chinese in post (any form of chinese)
# 3) channel discription is also not english
# 4) may be leave 10 post for each of those channel

import plain_db
from telegram_util import removeOldFiles, matchKey
import dbase
from dbase import index, maintext, timestamp, channels, suspect
from common import log_call
import time
from telegram_util import isCN

def getScore(key):
	c_score = channels.get(key.split('/')[0])
	score = (timestamp.get(key, 0) - 
		c_score * 1000)
	if c_score == -2:
		return 1
	if c_score == -1:
		return 0
	return -score

@log_call()
def cleanupRedundant():
	bucket = {}
	for key, text in maintext.items():
		if key.endswith('/0'):
			continue
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
		for score, key in key_score[10:]:
			dbase.removeKey(key)
			count += 1
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

def notCNEN(text):
	if not text:
		return True
	for c in text:
		if isCN(c):
			return False
	# TODO: keep en channel as well, for now, delete them
	return True

def cleanupChannel(keys, keepChinese=True):
	if not keys or len(keys) <= 100:
		return 0 
	if keepChinese:
		result_keys = []
		for key in keys:
			if notCNEN(index.get(key)):
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

def cleanupChannelNonCNEN(keys):
	result_keys = []
	for key in keys:
		if notCNEN(index.get(key)):
			result_keys.append(key)
	sort_keys = [(getKeyScore(key), key) for key in result_keys]
	sort_keys.sort(reverse=True)
	count = 0
	for key in sort_keys[100:]:
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
		if channels.get(channel) == -2:
			for key in bucket[channel]:
				dbase.removeKey(key)
	for channel in suspect.items():
		if channels.get(channel) > 5:
			count += cleanupChannel(bucket.get(channel))
	print('cleanupSuspect', count)

@log_call()
def cleanupBad():
	

@log_call()
def cleanupNonCNEN():
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
		if channels.get(channel) < 5:
			continue
		desc = index.get(channel + '/0')
		if notCNEN(desc):
			count += cleanupChannelNonCNEN(bucket.get(channel))
	print('cleanupNonCNEN', count)

@log_call()
def save():
	index.save_dont_call_in_prod()
	maintext.save_dont_call_in_prod()
	timestamp.save_dont_call_in_prod()
	channels.save_dont_call_in_prod()
	# removeOldFiles('tmp', day = 2)

if __name__ == '__main__':
	cleanupBad()
	save()
	cleanupNonCNEN()
	save()
	cleanupRedundant()
	save()
	cleanupNoMain()
	save()
	cleanupSuspect()
	save()
