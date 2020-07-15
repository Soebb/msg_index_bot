# move to html parsemode
#
# potential improvements
# limit raw result
# skip sort by time

from common import debug_group
import dbase
from dbase import maintext, blocklist, index, channels, timestamp, core_index
from telegram_util import matchKey
import itertools
import time

def finalTouch(result):
	final_result = ['%d. <a href="https://t.me/%s">%s</a>' % (
		result_index + 1, r[0], r[1]) 
		for result_index, r in enumerate(
			itertools.islice(result, 20))]
	return final_result

def searchHit(targets, text):
	r = [target.lower() in text.lower() for target in targets]
	return sum(r) == len(r)

def searchRaw(targets):
	count = 0
	for key, value in list(core_index.items()):
		if searchHit(targets, value):
			count += 1
			yield key
	print('searchRaw', count)
	if count < 20:
		for key, value in index.items():
			if searchHit(targets, value):
				count += 1
				yield key

def flipFirst(result, func, sendAfter=True):
	rest = []
	for key in result:
		if func(key):
			yield key
		else:
			rest.append(key)
	if sendAfter:
		for key in rest:
			yield key

def dedupResult(result, func, sendAfter=True):
	cache = set()
	rest = []
	for key in result:
		text = func(key)
		if not text:
			continue
		if text in cache:
			rest.append(key)
			continue
		cache.add(text)
		yield key
	if sendAfter:
		for key in rest:
			yield key

def shouldFlipFirst(key):
	channel = key.split('/')[0]
	if channels.get(channel) == -1:
		return False
	if channels.get(channel) < 5:
		return True
	return not matchKey(index.get(key), blocklist.items())

def populateMaintext(result):
	for key in result:
		yield key, maintext.get(key)

def getChannelTitle(key):
	channel = key.split('/')[0]
	return maintext.get(channel + '/0')

def populateChannelTitle(result):
	for key in result:
		yield key, getChannelTitle(key)	

def searchTextRaw(targets):
	result = searchRaw(targets)
	result = [(timestamp.get(key, 0), key) for key in result]
	result.sort(reverse=True)
	result = [item[1] for item in result]
	result = flipFirst(result, lambda key: channels.get(
		key.split('/')[0]) != -2, sendAfter=False)
	result = dedupResult(result, lambda key: maintext.get(
		key), sendAfter=False)
	result = flipFirst(result, lambda key: searchHit(
		targets, maintext.get(key)))
	result = dedupResult(result, lambda key: key.split('/')[0])
	result = flipFirst(result, lambda key: shouldFlipFirst(key))
	return result

def searchText(text):
	targets = text.split()
	result = searchTextRaw(targets)
	result = populateMaintext(result)
	return finalTouch(result)

def searchChannel(text):
	targets = text.split()
	result = searchTextRaw(targets)
	result = dedupResult(result, lambda key: getChannelTitle(
		key), sendAfter=False)
	result = populateChannelTitle(result)
	return finalTouch(result)