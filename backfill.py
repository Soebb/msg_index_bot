from common import sendDebugMessage, log_call, isSimplified
import time
import random
import sys
import webgram
import dbase
from dbase import index, channels

if 'test' in sys.argv:
	time_limit = 1
else:
	time_limit = 20 * 60

@log_call()
def quickBackfill(channel):
	start_time = time.time()
	post_id = 1
	while True:
		posts = webgram.getPosts(channel, post_id)
		for post in posts[1:]:
			dbase.update(post)
		if post_id == posts[-1].post_id + 1:
			break
		post_id = posts[-1].post_id + 1
		if post_id % 100 == 0 and time.time() - start_time > time_limit:
			break
	print('quickBackfill end', channel, post_id)

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
				print(left, right, post_id, hit)
				break
			print(left, right, post_id, hit)
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
	sendDebugMessage('slowBackfill', channel, post_id)
	found_new_key = False
	start_time = time.time()
	while post_id > 0:
		post = webgram.getPost(channel, post_id)
		if post.getIndex():
			if not index.get(post.getKey()):
				found_new_key = True
			if not found_new_key:
				print('slowBackfill jump', channel, post_id)
				post_id -= 100
			dbase.update(post)
		if post_id % 100 == 0:
			if time.time() - start_time > time_limit:
				break
		post_id -= 1
	print('slowBackfill end', channel, post_id)

def shouldBackfill(channel):
	post = webgram.get(channel)
	if not post.exist:
		return False
	dbase.update(post)
	if channel in ['what_youread', 'dushufenxiang_chat']:
		return True
	if channels.get(channel) in [0, 1] and random.random() < 0.05:
		return True
	if dbase.suspectBadChannel(post):
		if channels.get(channel) >= 0:
			print('suspectBadChannel', channel)
		return False
	return isSimplified(post.getIndex()) and random.random() < 0.05

def backfill(channel):
	if not shouldBackfill(channel):
		return 
	if len(webgram.getPosts(channel, 1)) > 1:
		quickBackfill(channel)
	else:
		slowBackfill(channel)