# move to html parsemode
#
# potential improvements
# limit raw result
# skip sort by time

from common import debug_group
import dbase
from dbase import maintext, blocklist, index, channels, timestamp, coreIndex, suspect, authors
from telegram_util import matchKey, isCN
import itertools
import time

def getHtmlReply(result):
	return ['%d. <a href="https://t.me/%s">%s</a>' % r for r in result]

def getMarkdownReply(result):
	return ['%d. [%s](https://t.me/%s)' % (r[0], r[2], r[1]) for r in result]

def finalTouch(result):
	return [(result_index + 1, r[0], r[1]) for 
		result_index, r in enumerate(itertools.islice(result, 40))]

def searchHit(target, item):
	if not item[1]:
		return False
	return matchKey(item[0] + item[1], [target])

def searchHitAll(targets, item):
	for target in targets:
		if not searchHit(target, item):
			return False
	return True

def searchRaw(targets, searchCore=False):
	if not targets: # optimization of /s and /sc
		return [x for x in list(coreIndex)[:1000] if index.get(x)]
	if searchCore:
		# after index cleanup, x might not in index anymore
		space = [(x, index.get(x)) for x in list(coreIndex) if index.get(x)]
	else:
		space = index.items()
	for target in targets:
		space = [item for item in space if searchHit(target, item)]
	return [item[0] for item in space]

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

def isCNIndex(key):
	text = index.get(key)
	if not text:
		return False
	for c in text:
		if isCN(c):
			return True
	return False

def shouldFlipFirstForChannel(key):
	channel = key.split('/')[0]
	if not key.endswith('/0'):
		return False
	if channel in suspect._db.items or channels.get(channel) == -1:
		return False
	return timestamp.get(key, 0) > time.time() - 24 * 7 * 60 * 60

def populateMaintext(result):
	for key in result:
		yield key, maintext.get(key)

def populateMaintextLoose(result):
	for key in result:
		yield key, (maintext.get(key) or 
			maintext.get(key.split('/') + '/0') or key)

def getChannelTitle(key):
	channel = key.split('/')[0]
	return maintext.get(channel + '/0')

def populateChannelTitle(result):
	for key in result:
		yield key, getChannelTitle(key)	

def populateChannelTitleLoose(result):
	for key in result:
		yield key, (getChannelTitle(key) or key.split('/')[0])

def sortAndClean(result):
	result = [(timestamp.get(key, 0) - 
		channels.get(key.split('/')[0]) * 1000, key) for key in result]
	result.sort(reverse=True)
	result = [item[1] for item in result]
	result = flipFirst(result, lambda key: channels.get(
		key.split('/')[0]) != -2, sendAfter=False)
	result = flipFirst(result, lambda key: isCNIndex(key))
	result = flipFirst(result, lambda key: (key.split('/')[0] 
		not in suspect._db.items))
	result = flipFirst(result, lambda key: key in coreIndex)
	return result

def searchTextRaw(targets, searchCore=False):
	result = searchRaw(targets, searchCore=searchCore)
	result = sortAndClean(result)
	result = flipFirst(result, lambda key: searchHitAll(
		targets, (key, maintext.get(key))))
	result = dedupResult(result, lambda key: key.split('/')[0])
	return result

def searchAuthor(text):
	text = text.replace(' ', '_')
	line = authors.get(text) or ''
	result = line.split()
	result = populateMaintextLoose(result)
	return finalTouch(result)

def searchAuthorChannel(text):
	text = text.replace(' ', '_')
	line = authors.get(text) or ''
	result = line.split()
	result = dedupResult(result, lambda key: key.split('/')[0], sendAfter=False)
	result = populateChannelTitleLoose(result)
	return finalTouch(result)

def searchRelated(text):
	text = text.split('/')[-1]
	if not text:
		return []
	result = set()
	for item in dbase.channelrefer.items():
		if text in item.split(':'):
			result.update(item.split(':'))
	result.discard(text)
	result = [channel + '/0' for channel in result 
		if maintext.get(channel + '/0')]
	result = sortAndClean(result)
	result = populateMaintext(result)
	return finalTouch(result)

def searchText(text, searchCore=False):
	targets = text.split()
	result = searchTextRaw(targets, searchCore=searchCore)
	result = dedupResult(result, lambda key: maintext.get(
		key), sendAfter=False)
	result = populateMaintext(result)
	return finalTouch(result)

def searchChannel(text, searchCore=False):
	targets = text.split()
	result = searchTextRaw(targets, searchCore=searchCore)
	result = flipFirst(result, lambda key: 
		shouldFlipFirstForChannel(key))
	result = dedupResult(result, lambda key: getChannelTitle(
		key), sendAfter=False)
	result = populateChannelTitle(result)
	return finalTouch(result)