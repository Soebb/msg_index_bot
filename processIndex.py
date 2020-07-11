from db import db

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

def processBubble(item):
	post_link = getPostLinkBubble(item)
	tryAddChannelBubble(post_link.strip('/').split('/')[-2], getOrigChannel(item))
	tryAddAllMentionedChannel(item, tryAddChannelBubble)
	text_fields_name = [
		'link_preview_title',
		'tgme_widget_message_text', 
		'tgme_widget_message_document_title', 
		'link_preview_description']
	text_fields = [getText(item, field) for field in text_fields_name]
	if ''.join(text_fields) == '':
		return
	[db.addIndex(post_link, text) for text in text_fields]
	db.setMainText(post_link, getCompact(getMainText(text_fields)))
	db.setTime(post_link, getTime(item))