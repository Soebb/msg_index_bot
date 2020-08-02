from common import sendDebugMessage, log_call, isSimplified
import time
import random
import sys
import webgram
import dbase
from dbase import index, channels, timestamp

if 'test' in sys.argv:
	time_limit = 10
else:
	time_limit = 10 * 60

@log_call()
def quickBackfill(channel):
	sendDebugMessage('quickBackfill start', '@' + channel)
	start_time = time.time()
	post_id = 1
	while True:
		posts = webgram.getPosts(channel, post_id)
		for post in posts[1:]:
			dbase.update(post)
		if post_id == posts[-1].post_id + 1:
			break
		post_id = posts[-1].post_id + 1
		if time.time() - start_time > time_limit:
			break
	sendDebugMessage('quickBackfill end', '@' + channel, post_id)

def getMaxInIndex(channel):
	result = 1
	for post, _ in index.items():
		if post.split('/')[0] == channel:
			result = max(result, int(post.split('/')[1]))
	return result

def _findLastMessage(channel):
	left = getMaxInIndex(channel)
	right = 10000 + left
	while left < right - 50:
		hit = False
		for _ in range(5):
			post_id = int(left + (random.random() * 0.75 + 0.25) * (right - left))
			post = webgram.getPost(channel, post_id)
			if post.getIndex():
				dbase.update(post)
				hit = True
				break
		mid = int((left + right) / 2)
		if hit:
			if post_id > mid:
				right = post_id * 2 - left
			left = post_id
		else:
			right = mid
	return left

@log_call()
def slowBackfill(channel):
	post_id = _findLastMessage(channel)
	sendDebugMessage('slowBackfill', '@' + channel, post_id)
	start_time = time.time()
	while post_id > 1:
		post_id -= 1
		key = channel + '/' + str(post_id)
		if index.get(key):
			post_id -= int(random.random() * 100)
			continue
		post = webgram.getPost(channel, post_id)
		if post.getIndex():
			dbase.update(post)
		if time.time() - start_time > time_limit:
			break
	print('slowBackfill end', '@' + channel, post_id)

def shouldBackfill(channel):
	if not dbase.isCNGoodChannel(channel):
		dbase.suspect.add(channel)
		return False
	dbase.suspect.remove(channel)
	return random.random() > 0.005

def backfill(channel):
	if not shouldBackfill(channel):
		return 
	if len(webgram.getPosts(channel, 1)) > 1:
		quickBackfill(channel)
	else:
		slowBackfill(channel)