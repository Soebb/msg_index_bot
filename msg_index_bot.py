#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail
from common import debug_group, tele, log_call, sendDebugMessage
from command import setupCommand
import threading
import random
import backfill
import clean
import sys
import dbase
from dbase import channels, coreIndex
import webgram
import time

@log_on_fail(debug_group)
@log_call()
def indexingImp():
	for channel, score in channels.items():
		if score < 0 or random.random() > 1.0 / min(
				score ** 2.5 + 1, score ** 2 * 2 + 1):
			continue
		if 'test' in sys.argv and random.random() > 0.1:
			continue # better testing
		if channel in dbase.delay._db.items and random.random() > 0.01:
			continue
		posts = webgram.getPosts(channel, 1) # force cache
		for post in posts:
			dbase.update(post)
		if len(posts) <= 1: # save http call
			continue
		dbase.updateAll(webgram.getPosts(channel))
		dbase.updateDelayStatus(channel)
	sendDebugMessage(*(['indexingImpDuration'] + dbase.resetStatus()), persistent=True)

@log_on_fail(debug_group)
@log_call()
def indexBackfill():
	last_record = time.time()
	for channel, score in channels.items():
		backfill.backfill(channel)
		if time.time() - last_record > 60 * 60:
			last_record = time.time()
			sendDebugMessage(*(['indexBackfillDuration'] + dbase.resetStatus()), persistent=True)
	sendDebugMessage(*(['indexBackfillDuration'] + dbase.resetStatus()), persistent=True)

@log_call()
def indexing():
	if len(coreIndex) == 0:
		dbase.fillCoreIndex()
	clean.indexClean() # testing
	if len(dbase.maintext.items()) > 2000000:
		clean.indexClean()
	indexingImp()
	indexBackfill()
	threading.Timer(1, indexing).start()

if __name__ == '__main__':
	setupCommand(tele.dispatcher)
	threading.Timer(1, indexing).start() 
	if 'nocommand' not in sys.argv:
		tele.start_polling()
		tele.idle()
