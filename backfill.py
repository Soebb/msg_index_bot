import time
import random
import sys
import webgram
import dbase
from dbase import index, channels, timestamp

YEAR = 365 * 60 * 60 * 24

def getMaxIteration(channel):
	score = channels.get(channel)
	return max(0, 10 - score) ** 3 + 20

def postTooOld(post):
	return post.time < max(dbase.getRetain(post.channel), time.time() - YEAR)

def quickBackfill(channel):
	posts = webgram.getPosts(channel)
	dbase.updateAll(posts)
	posts = posts[1:]
	for _ in range(getMaxIteration(channel)):
		if not posts or postTooOld(posts[0]):
			return
		post_id = posts[0].post_id
		posts = webgram.getPosts(channel, post_id, direction='before')[1:]
		dbase.updateAll(posts)
		
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

def slowBackfill(channel):
	post_id = _findLastMessage(channel)
	findNew = False
	for _ in range(getMaxIteration(channel)):
		post_id -= 1
		if post_id <= 1:
			break
		key = channel + '/' + str(post_id)
		if index.get(key):
			post_id -= int(random.random() * 100)
			continue
		post = webgram.getPost(channel, post_id)
		if post.getIndex():
			findNew = True
			dbase.update(post)
		elif findNew:
			dbase.removeKey(key)
		if postTooOld(post):
			break

def shouldBackfill(channel):
	if random.random() > 0.005:
		return False
	
	if not dbase.isCNGoodChannel(channel):
		dbase.suspect.add(channel)
		return False
	dbase.suspect.remove(channel)

	if channel in dbase.delay._db.items and random.random() > 0.1:
		return False
	return True

def backfill(channel):
	if not shouldBackfill(channel):
		return 
	if len(webgram.getPosts(channel, 1)) > 1:
		quickBackfill(channel)
	else:
		slowBackfill(channel)