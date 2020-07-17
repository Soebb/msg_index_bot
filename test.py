status = {}

def inc():
	status['time'] = status.get('time', 0) + 1

inc()