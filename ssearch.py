
def _finalTouch(result):
	final_result = result[:20]
	final_result = ['%d. [%s](https://t.me/%s)' % (index + 1, x[0], x[1]) 
		for index, x in enumerate(final_result)]
	return final_result

def _hit(targets, text):
	r = [target.lower() in text.lower() for target in targets]
	return sum(r) == len(r)

def _searchRaw(targets):
	for key, value in db.index.getItems():
		if _hit(targets, value):
			yield key

def searchChannel(text):
	targets = text.split()
	hit_count = {}
	total_count = {}
	posts = {}
	for key, value in db.index.getItems():
		channel = key.split('/')[0]
		if _hit(targets, value):
			hit_count[channel] = hit_count.get(channel, 0) + 1 
			if _hit(targets, db.maintext.get(key, '')) or channel not in posts:
				posts[channel] = key
		total_count[channel] = total_count.get(channel, 0) + 1 
	raw_result = [(hit_count[key] * 1.0 / total_count[key], key) 
		for key in hit_count]
	raw_result.sort(reverse=True)
	result = []
	for _, channel in raw_result:
		name = db.maintext.get(channel + '/0') or db.channelname.get(channel)
		if not name:
			continue
		result.append((name, posts[channel]))
	result = ([x for x in result if _hit(targets, x[0])] + 
		[x for x in result if not _hit(targets, x[0])])
	return _finalTouch(result)

def searchText(text):
	targets = text.split()
	result = list(_searchRaw(targets))
	result = [(db.time.get(x, 0), x) for x in result]
	result.sort(reverse=True)
	
	exist_maintext = set()
	exist_channel = set()
	first = []
	rest = []
	resttop = []
	for _, x in result:
		main_text = db.maintext.get(x)
		channel = x.split('/')[0]
		if not main_text or main_text in exist_maintext:
			continue
		exist_maintext.add(main_text)
		item = (main_text, x)
		if db.badScore(item) >= 20:
			continue
		if (db.badScore(item) > 0 and 
			db.channels.get(channel, 100) > 0):
			rest.append(item)
		elif channel in exist_channel:
			resttop.append(item)
		else:
			first.append(item)
		exist_channel.add(channel)

	result = ([x for x in first if _hit(targets, x[0])] + 
		[x for x in first if not _hit(targets, x[0])] + 
		resttop + rest)
	return _finalTouch(result)