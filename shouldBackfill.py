from telegram_util import isCN
import random
import hanzidentifier
from channel import Channel
from processIndex import processChannelInfo
from db import db

def _isMostCN(text):
	if not text or not text.strip():
		return False
	cn = sum([isCN(c) + hanzidentifier.is_simplified(c) for c in text])
	for c in text:
		if isCN(c) and not hanzidentifier.is_simplified(c):
			return False
	return cn * 2 >= len(text)

def shouldBackfill(channel, score):
	if channel in ['what_youread']:
		return True
	c = Channel(channel)
	if not c.exist():
		return False
	processChannelInfo(channel, c.getSoup())
	if score <=1 and random.random() < 0.05:
		return True
	if db.isBadFromReferRelate(channel):
		return False
	description = db.index.get(channel + '/0')
	if db.badScore(description):
		return False
	return _isMostCN(description) and random.random() < 0.05