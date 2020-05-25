import time, datetime

class Logging:
	def __init__(self, filename):
		dt = datetime.datetime.today()
		self.fd = open('./logs/{}-{}-{}_{}:{}:{}.log'.format(dt.day, dt.month, dt.year, dt.hour, dt.minute, dt.second), 'a')
		self.closed = False
		self.polllist = []
	def _write(self, state, data):
		prefix = 0
		if state == 'main':
			prefix = 0
		if state == 'server':
			prefix = 1
		if state == 'console':
			prefix = 2
		self.fd.write(str(prefix) + data + '\n')
		self.fd.flush()
		for i in self.polllist:
			i.add(str(prefix)+data)
	def error(self, state, string):
		dt = datetime.datetime.today()
		self._write(state, '[{}-{}-{} {}:{}:{} ERROR] :: {}'.format(dt.day, dt.month, dt.year, dt.hour, dt.minute, dt.second, string))
	def info(self, state, string):
		dt = datetime.datetime.today()
		self._write(state, '[{}-{}-{} {}:{}:{} INFO] :: {}'.format(dt.day, dt.month, dt.year, dt.hour, dt.minute, dt.second, string))
	def raw(self, string):
		self._write('server', string[:-1])

	def close(self):
		self.fd.close()
		self.closed = True
	def add2poll(self, wherepoll):
		self.polllist.append(wherepoll)