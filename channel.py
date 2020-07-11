from bs4 import BeautifulSoup
import cached_url

def getButtonText(soup):
	item = soup.find('a', class_='tgme_action_button_new')
	return (item and item.text) or ''

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

	def save(self, db, referer=None):
		if not self.exist():
			return
		db.addChannel(self.name, referer)