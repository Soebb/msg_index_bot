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

@log_on_fail(debug_group)
def backfillBotChannel(channel):
	main_msg = tele.bot.send_message(channel, 'test')
	main_msg.delete()
	for mid in range(2200, 2500): # main_msg.message_id
		try:
			msg = tele.bot.forward_message(debug_group.id,
				main_msg.chat_id, mid)
			msg.delete()
		except:
			continue
		if mid % 100 == 0:
			sendDebugMessage('backfillBotChannel1 ' + str(mid))
			db.save()
			commitRepo(delay_minute=0)
			sendDebugMessage('backfillBotChannel2 ' + str(mid))
		indexFromTelegramMsg(msg)
	db.save()
	commitRepo(delay_minute=0)