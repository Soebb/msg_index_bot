from db import db
from processIndex import processBubble, processChannelInfo
from debug import sendDebugMessage
import time

def _canUseQuickBackfill(channel):
	link = 'https://t.me/s/%s/1' % channel
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	processChannelInfo(channel, soup)
	return soup.find('div', class_='tgme_widget_message_bubble')

@log_call()
def _quickBackfillChannel(channel):
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

def _getItem(channel, index):
	prefix = 'https://t.me/%s/' % channel
	link = prefix + str(index) + '?embed=1'
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	if (not soup.find('div', class_='tgme_widget_message_text') and 
		not soup.find('div', class_='tgme_widget_message_document_title')):
		return
	item = soup.find('div', class_='tgme_widget_message_bubble')
	if item:
		processBubble(item)
	return item

def _findLastMessage(channel):
	left = 1
	right = 300000
	while left < right - 100:
		item = None
		for _ in range(5):
			index = int(left + (random.random() * 0.5 + 0.25) * (right - left))
			item = _getItem(channel, index)
			if item:
				break
		if item:
			left = index
		else:
			right = int((left + 3 * right) / 4)
	return left

@log_call()
def _slowBackfillChannel(channel):
	post = _findLastMessage(channel)
	sendDebugMessage('slowBackfillChannel findIndex', channel, post)
	existing_index = set([None])
	new_index = set()
	start_time = time.time()
	while post > 0:
		post_link = channel + '/' + str(post)
		existing_index.add(db.index.items.get(post_link))
		if not _getItem(channel, post):
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

def shouldBackfill(channel, score):
	

def backfillChannel(channel):
	if _canUseQuickBackfill(channel):
		_quickBackfillChannel(channel)
	else:
		_slowBackfillChannel(channel)