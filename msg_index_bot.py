#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# move to html parsemode

# do I need a CN related util?

from telegram.ext import MessageHandler, Filters
from channel import Channel
from telegram_util import log_on_fail, cutCaption, splitCommand
import threading
from bs4 import BeautifulSoup
import cached_url
import random
# from debug import debug_group, tele, sendDebugMessage, log_call
from processIndex import processBubble, processChannelInfo
from shouldBackfill import shouldBackfill
import sys
from fetchIndex import backfillChannel
from dbase import index, maintext, channelrefer, timestamp, channels, blocklist
import webgram

@log_on_fail(debug_group)
@log_call()
def indexingImp():
	for channel, score in channels.getItems():
		if score < 0 or random.random() > 1.0 / (score * score + 1):
			continue
		for post in webgram.getPosts(channel):
			dbase.update(post)

@log_on_fail(debug_group)
@log_call()
def backfill():
	for channel, score in db.channels.getItems():
		if shouldBackfill(channel, score):
			backfillChannel(channel)

@log_call()
def indexing():
	indexingImp()
	backfill()
	threading.Timer(60, indexing).start()

if __name__ == '__main__':
	setupCommand(tele.dispatcher)
	threading.Timer(1, indexing).start() 
	tele.start_polling()
	tele.idle()
