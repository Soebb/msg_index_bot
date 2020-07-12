import os

def _getFile(name, value_int=False):
	start = 1
	result = {}
	while True:
		fn = name + str(start)
		if not os.path.exists(fn):
			break
		with open(fn) as f:
			for line in f.readlines():
				line = line.strip()
				if not line:
					continue
				key = line.split()[0]
				value = line[len(key) + 1:]
				if value_int:
					value = int(value)
				result[key] = value
		start += 1
	return result

class DBItem(object):
	def __init__(self, name, value_int = False, random_save = False):
		self.random_save = random_save
		self.fn = 'mydb/' + name
		self.items = _getFile(self.fn, value_int)
		self.op_count = 0

	def _add(self, key, value):
		if key in self.items:
			raise Exception('key should not exist', key, self.fn)
		self.items[key] = value
		with open(self.fn + '1', 'a') as f:
			f.write('\n' + key + ' ' + str(value))

	def update(self, key, value):
		if key not in self.items:
			self._add(key, value)
		self.items[key] = value
		self.op_count += 1
		if self.op_count % 100 == 0:
			self.save()

	def updateIfLarger(self, key, value):
		oldValue = self.items.get(key, 0)
		value = max(value, oldValue)
		self.update(key, value)

	def inc(self, key):
		if key not in self.items:
			self._add(key, 1)
			return
		self.update(key, self.items[key] + 1)

	def remove(self, key):
		if key in self.items:
			del self.items[key]

	def get(self, key, default = None):
		return self.items.get(key, default)

	def save(self):
		lines = self.items # .copy()
		lines = [key + ' ' + str(lines[key]) for key in lines]
		lines.sort()
		limit = 10000
		start = 0
		while True:
			towrite = '\n'.join(lines[limit * start:limit * (start + 1)])
			if not towrite:
				break
			start += 1
			fn = self.fn + str(start)
			with open(fn + 'tmp', 'w') as f:
				f.write(towrite)
			os.system('mv %stmp %s' % (fn, fn))
		while True:
			start += 1
			r = os.system('rm %s%d > /dev/null 2>&1' % (self.fn, start))
			if r != 0:
				break

	def getItems(self):
		return list(self.items.items())