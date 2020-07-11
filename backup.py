@log_on_fail(debug_group)
def searchBigGroup():
	sendDebugMessage('start searchBigGroup')
	result = []
	count = 0
	for channel, _ in db.channels.items.items():
		count += 1
		if count % 100 == 0:
			sendDebugMessage('start searchBigGroup ' + str(count))
		c = Channel(channel)
		if not c.exist() or not isMostCN(c.getTitle()):
			continue
		result.append((c.getActiveCount(), channel))
	result.sort(reverse=True)
	result = result[:100]
	result = ['[%s](https://t.me/%s)' % (x[1], x[1]) for x in result]
	debug_group.send_message('\n'.join(result), disable_web_page_preview = True, parse_mode = 'Markdown')
