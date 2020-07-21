import plain_db
from telegram_util import removeOldFiles
import dbase
from dbase import index, maintext, timestamp, channels
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
def cleanup1():
	bucket = {}
	for key, text in maintext.items():
		text = text[:10]
		if text in bucket:
			bucket[text].append(key)
		else:
			bucket[text] = [key]
	print('cleanup1 1')
	for text, keys in bucket.items():
		key_score = [(getScore(key), key) for key in keys]
		key_score.sort()
		for score, key in key_score[1:]:
			dbase.removeKey(key)
			print('remove key', key)
		if key_score[0][0] == 102:
			dbase.removeKey(key_score[0][1])
		else:
			print('keep key', key_score[0][1])

@log_call()
def cleanup2():
	plain_db.cleanupLargeDB('index')
	plain_db.cleanupLargeDB('maintext')
	plain_db.cleanupLargeDB('timestamp')
	plain_db.cleanupLargeDB('channelrefer')
	plain_db.cleanupLargeDB('channels')
	removeOldFiles('tmp', day = 1)

if __name__ == '__main__':
	cleanup1()
	cleanup2()
