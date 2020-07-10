from bs4 import BeautifulSoup
import cached_url
from telegram_util import cutCaption
from helper import getButtonText

def getCompact(text):
	if not text:
		return '' 
	return cutCaption(' '.join(text.split()), '', 50)

def getCount(text):
	try:
		return int(''.join(text.split()[:-1]))
	except:
		print(text)
		return 0

class Channel(object):
	def __init__(self, name):
		self.name = name
		self.link = 'https://t.me/' + name

	def exist(self):
		content = cached_url.get(self.link, force_cache=True)
		if 'tgme_page_title' not in content:
			return False
		soup = BeautifulSoup(content, 'html.parser')
		if 'Send Message' in getButtonText(soup):
			return False
		return True

	def getSoup(self):
		content = cached_url.get(self.link, force_cache=True)
		return BeautifulSoup(content, 'html.parser')

	def getRep(self):
		soup = self.getSoup()
		title = getCompact(soup.find('div', class_='tgme_page_title').text)
		return '[%s](%s)' % (title, self.link)

	def getTitle(self):
		soup = self.getSoup()
		return soup.find('div', class_='tgme_page_title').text

	def getActiveCount(self):
		soup = self.getSoup()
		member = soup.find('div', class_='tgme_page_extra')
		if not member:
			return 0
		member_block = member.text.split(',')
		if len(member_block) <= 1:
			return 0
		return getCount(member_block[1])

	def save(self, db, referer=None):
		if not self.exist():
			return
		db.addChannel(self.name, referer)

	def getLink(self):
		return self.link