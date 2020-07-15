from processIndex import processBubble, processChannelInfo
from debug import sendDebugMessage, log_call
import time
import random
import sys
from bs4 import BeautifulSoup
import cached_url

if 'test' in sys.argv:
	time_limit = 15
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
			return
		post_id = posts[-1].post_id + 1
		if post_id % 100 == 0 and time.time() - start_time > time_limit:
			return

def _findLastMessage(channel):
	left = 1
	right = 1000
	while left < right - 30:
		item = None
		for _ in range(5):
			index = int(left + (random.random() * 0.75 + 0.25) * (right - left))
			post = webgram.getPost(channel, index)
			if post.exist:
				dbase.update(post)
				break
		right_bound = int((left + 3 * right) / 4)
		if item:
			left = index
			if left > right_bound:
				right = int(right * 4 / 3)
		else:
			right = right_bound
	return left

@log_call()
def slowBackfill(channel):
	post_id = _findLastMessage(channel)
	sendDebugMessage('slowBackfill', channel, post_id)
	found_new_key = False
	start_time = time.time()
	while post_id > 0:
		post = webgram.get(channel, post_id)
		if dbase.isNewPost(post):
			found_new_key = True
		dbase.update(post)
		if post.getIndex() and not found_new_key:
			post -= 100
		if post % 100 == 0:
			if time.time() - start_time > time_limit:
				return
		post -= 1

def isSimplified(text):
	cn = sum([isCN(c) + hanzidentifier.is_simplified(c) for c in text])
	for c in text:
		if isCN(c) and not hanzidentifier.is_simplified(c):
			return False
	return cn * 2 >= len(text)

def shouldBackfill(channel):
	post = webgram.get(channel)
	if not post.exist:
		return False
	dbase.update(post)
	if channel in ['what_youread']:
		return True
	if channels.get(channel) in [0, 1] and random.random() < 0.05:
		return True
	if dbase.suspectBadChannel(post):
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