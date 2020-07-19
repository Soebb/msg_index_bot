import time
print(time.time())
import dbase
dbase.maintext.load()
print(time.time())
dbase.index.load()
print(time.time())