import time, datetime

class Logging:
	def __init__(self, debug):
		self.s_debug = debug
		dt = datetime.datetime.today()
		self.fd = open('./logs/{}-{}-{}_{}:{}:{}.log'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second), 'a')
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
			i.put('all', str(prefix)+data)
	def error(self, state, string):
		dt = datetime.datetime.today()
		self._write(state, '[{}-{}-{} {}:{}:{} ERROR] :: {}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, string))
	def info(self, state, string):
		dt = datetime.datetime.today()
		self._write(state, '[{}-{}-{} {}:{}:{} INFO] :: {}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, string))
	def raw(self, string):
		self._write('server', string[:-1])
	def warning(self, state, string):
		dt = datetime.datetime.today()
		self._write(state, '[{}-{}-{} {}:{}:{} WARNING] :: {}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, string))
	def debug(self, state, string):
		if not self.s_debug:
			return
		dt = datetime.datetime.today()
		self._write(state, '[{}-{}-{} {}:{}:{} DEBUG] :: {}'.format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, string))

	def get_past_lines(self):
		with open(self.fd.name, 'r') as lines:
			return lines.split('\n')

	def close(self):
		self.fd.close()
		self.closed = True
	def add2poll(self, wherepoll):
		self.polllist.append(wherepoll)