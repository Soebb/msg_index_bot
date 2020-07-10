def getButtonText(soup):
	item = soup.find('a', class_='tgme_action_button_new')
	return (item and item.text) or ''