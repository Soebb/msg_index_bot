from db import db
from channel import Channel
from datetime import datetime
from common import getCompact, addChannelRaw

def getPostLinkBubble(item):
	try:
		result = item.find('a', class_='tgme_widget_message_forwarded_from_name')['href']
		int(result.strip('/').split('/')[-1])
		return result
	except:
		return item.find('a', class_='tgme_widget_message_date')['href']

def getOrigChannel(item):
	orig_link = item.find('a', class_='tgme_widget_message_date')['href']
	return orig_link.strip('/').split('/')[-2]

def addMentionedChannel(item, referer):
	if not item:
		return
	for link in item.find_all('a'):
		link = link.get('href', '')
		addChannelRaw(link, referer)

def getText(item, class_name):
	try:
		return item.find('div', class_=class_name).text
	except:
		return ''

def getMainText(text_fields):
	if text_fields[0] and len(text_fields[0]) > 5:
		return text_fields[0]
	for x in text_fields[1:] + [text_fields[0]]:
		if x:
			return x

def getTime(item):
	try:
		s = (item.find('a', class_='tgme_widget_message_date').
				find('time')['datetime'][:-6])
	except:
		print(item.find('a', class_='tgme_widget_message_date'))
		return 0
	format = '%Y-%m-%dT%H:%M:%S'
	return datetime.strptime(s, format).timestamp()

def getChannelTitle(soup):
	item = (soup.find('div', class_='tgme_channel_info_header_title') or 
		soup.find('div', class_='tgme_page_title'))
	if not item:
		return ''
	return getCompact(item.text, 10)

def processChannelInfo(channel, soup):
	title = getChannelTitle(soup)
	if not title:
		return
	description = (soup.find('div', class_='tgme_channel_info_description') or
		soup.find('div', class_='tgme_page_description'))
	addMentionedChannel(description, channel)
	description = title + ((description and description.text) or '')
	post_link = channel + '/0'
	db.addIndex(post_link, description)
	db.setMainText(post_link, title)

def hasLink(item):
	if item.find('div', class_='tgme_widget_message_document_title'):
		return True
	text = item.find('div', class_='tgme_widget_message_text')
	if not text:
		return False
	return text.find('a')

def hasFile(item):
	return item.find('div', class_='tgme_widget_message_document_title')

def processBubble(item):
	post_link = getPostLinkBubble(item)
	channel = post_link.strip('/').split('/')[-2]
	Channel(channel).save(db, getOrigChannel(item))
	addMentionedChannel(item, channel)
	text_fields_name = [
		'link_preview_title',
		'tgme_widget_message_text', 
		'tgme_widget_message_document_title', 
		'link_preview_description']
	text_fields = [getText(item, field) for field in text_fields_name]
	if ''.join(text_fields) == '':
		return
	[db.addIndex(post_link, text) for text in text_fields]
	if hasLink(item):
		db.addIndex(post_link, 'hasLink')
	if hasFile(item):
		db.addIndex(post_link, 'hasFile')
	db.setMainText(post_link, getCompact(getMainText(text_fields)))
	db.setTime(post_link, getTime(item))