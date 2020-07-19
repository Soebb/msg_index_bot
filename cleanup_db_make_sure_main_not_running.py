import plain_db
from telegram_util import removeOldFiles

if __name__ == '__main__':
	plain_db.cleanupLargeDB('index')
	plain_db.cleanupLargeDB('maintext')
	removeOldFiles('tmp', day = 7)
	print('finish')