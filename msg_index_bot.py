#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail
from common import debug_group, tele, log_call
from command import setupCommand
import threading
import random
import backfill
import sys
import dbase
from dbase import channels
import webgram

@log_on_fail(debug_group)
@log_call()
def indexingImp():
	for channel, score in channels.items():
		if score < 0 or random.random() > 1.0 / (score * score + 1):
			continue
		if 'test' in sys.argv and random.random() > 0.1:
			continue # better testing
		for post in webgram.getPosts(channel):
			dbase.update(post)

@log_on_fail(debug_group)
@log_call()
def indexBackfill():
	channels.items(123)
	for channel, score in channels.items():
		backfill.backfill(channel)

@log_call()
def indexing():
	indexingImp()
	indexBackfill()
	threading.Timer(1, indexing).start()

if __name__ == '__main__':
	setupCommand(tele.dispatcher)
	threading.Timer(1, indexing).start() 
	tele.start_polling()
	tele.idle()
