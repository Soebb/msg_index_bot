from db import db
from processIndex import processBubble
from debug import sendDebugMessage
import time

# backfillmode, file, link, all

def canUseQuickBackfill(channel):
	link = 'https://t.me/s/%s/1' % channel
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	return soup.find('div', class_='tgme_widget_message_bubble')

@log_call()
def quickBackfillChannel(channel):
	start_time = time.time()
	start = 1
	prefix = 'https://t.me/s/%s/' % channel
	while True:
		original_start = start
		link = prefix + str(start)
		soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
		for item in soup.find_all('div', class_='tgme_widget_message_bubble'):
			processBubble(item)
			post_link = item.find('a', class_='tgme_widget_message_date')['href']
			post_id = int(post_link.split('/')[-1])
			start = max(start, post_id + 1)
		if start % 100 == 0 and time.time() - start_time > 20 * 60:
			break
		if start == original_start:
			break
	db.save()

def getItem(channel, index, callback):
	prefix = 'https://t.me/%s/' % channel
	link = prefix + str(index) + '?embed=1'
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	if (not soup.find('div', class_='tgme_widget_message_text') and 
		not soup.find('div', class_='tgme_widget_message_document_title')):
		return
	item = soup.find('div', class_='tgme_widget_message_bubble')
	if item:
		callback(item)
	return item

def findLastMessage(channel, callback):
	left = 1
	right = 300000
	while left < right - 100:
		item = None
		for _ in range(5):
			index = int(left + (random.random() * 0.5 + 0.25) * (right - left))
			item = getItem(channel, index, callback)
			if item:
				break
		if item:
			left = index
		else:
			right = int((left + 3 * right) / 4)
	return left

@log_call()
def slowBackfillChannel(channel):
	post = findLastMessage(channel, callback)
	sendDebugMessage('slowBackfillChannel findIndex', channel, post)
	existing_index = set([None])
	new_index = set()
	start_time = time.time()
	while post > 0:
		post_link = channel + '/' + str(post)
		existing_index.add(db.index.items.get(post_link))
		if not getItem(channel, post, callback):
			db.remove(post_link)
		new_item = db.index.items.get(post_link)
		if new_item not in existing_index:
			new_index.add(new_item)
		if post % 100 == 0:
			if time.time() - start_time > 20 * 60:
				break
		if len(new_index) == 0 and len(existing_index) > 5:
			post -= 100
			existing_index = set()
		post -= 1
	db.save()

def backfillChannel(channel):
	if canUseQuickBackfill(channel):
		quickBackfillChannel(channel)
	else:
		slowBackfillChannel(channel)