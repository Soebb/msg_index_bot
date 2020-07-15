import plain_db

blocklist = plain_db.loadLargeDB('blocklist', isIntValue = True)
channels = plain_db.loadLargeDB('channels', isIntValue = True)
index = plain_db.loadLargeDB('index')
maintext = plain_db.loadLargeDB('maintext')
timestamp = plain_db.loadLargeDB('timestamp', isIntValue = True)
channelrefer = plain_db.loadLargeDB('channelrefer', isIntValue = True)
channelname = plain_db.loadLargeDB('channelname') 