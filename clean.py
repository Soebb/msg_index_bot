from common import log_call, debug_group
from telegram_util import log_on_fail
from dbase import channels, timestamp, index, maintext, suspect
import dbase

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

@log_call()
def cleanupRedundant():
	items = [(item[0], item[1][:10]) for item in maintext.items()]
	items = [item for item in items if not item[0].endswith('/0')]
	bucket = createBucket(items)
	print('cleanupRedundant bucket size', len(bucket.items()))
	count = 0
	for text, keys in bucket.items():
		key_score = [(getScore(key), key) for key in keys]
		key_score.sort()
		for score, key in key_score[1:]:
			dbase.removeKey(key)
			count += 1
	print('cleanupRedundant removed %d items' % count)

@log_on_fail(debug_group)
@log_call()
def indexClean():
	cleanupRedundant()
	save()
	