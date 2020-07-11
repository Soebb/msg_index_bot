from db import db
from processIndex import processBubble
import time

# backfillmode, file, link, all

def canUseQuickBackfill(channel):
	link = 'https://t.me/s/%s/1' % channel
	soup = BeautifulSoup(cached_url.get(link, force_cache=True), 'html.parser')
	return soup.find('div', class_='tgme_widget_message_bubble')

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

def slowBackfillChannel(channel, callback, db, total = 500):
	max_index = findLastMessage(channel, callback)
	print('backfillChannelNew findIndex', channel, max_index)
	existing_index = set([None])
	new_index = set()
	post = max(1, max_index - total)
	start_time = time.time()
	while post < max_index:
		post_link = channel + '/' + str(post)
		existing_index.add(db.index.items.get(post_link))
		if not getItem(channel, post, callback):
			db.remove(post_link)
		new_item = db.index.items.get(post_link)
		if new_item not in existing_index:
			new_index.add(new_item)
		if post % 100 == 0:
			print('jumpinfo', channel, post, len(existing_index), len(new_index))
			if time.time() - start_time > 20 * 60:
				break
		if len(new_index) == 0 and len(existing_index) > 5:
			print('jump', channel)
			post += 100
			existing_index = set()
		post += 1
	db.save()

def backfillChannel(channel, )