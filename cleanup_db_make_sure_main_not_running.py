import plain_db
from telegram_util import removeOldFiles
import dbase
from dbase import index, maintext, timestamp
from common import log_call

def cleanup1():
	...

log_call()
def cleanup2():
	plain_db.cleanupLargeDB('index')
	plain_db.cleanupLargeDB('maintext')
	plain_db.cleanupLargeDB('timestamp')
	plain_db.cleanupLargeDB('channelrefer')
	plain_db.cleanupLargeDB('channels')
	removeOldFiles('tmp', day = 0.5)

if __name__ == '__main__':
	cleanup1()
	cleanup2()
