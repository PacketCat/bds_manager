from subprocess import Popen, PIPE
import shutil
import os, time, zipfile
class Handler:
	def __init__(self, levelname, log, backupinter):
		self.log = log
		self.last_backup = 0
		self.b_interval = backupinter

		if not os.path.exists('./worlds/{}'.format(levelname)): 
			log.error('main', 'World not found >> returning;')
			return -1

		log.info('main','Copying directory')
		shutil.copytree('./worlds/{}'.format(levelname), './environ/worlds/')
		log.info('main','Renaming directory')
		os.rename('./environ/worlds/{}'.format(levelname), './environ/worlds/main')

		self.proccess = Popen(['./bedrock_server'], cwd='./environ/', stdin=PIPE, stdout=PIPE)
		os.set_blocking(self.proccess.stdin.fileno(), False)

		log.info('main', 'Changing loging state: main >> server')

	def _check_b(self):
		if self.last_backup < time.time():
			self._backup()
			self.last_backup = int(time.time) + self.b_interval

	def _backup(self):
		pass

	def get(self):
		return self.proccess.stdout.readline().decode()

	def put(self, data):
		buf = data.encode() +b '\n'
		return self.proccess.stdin.write(data)

	def stop(self, reason):
		buf = 'kick @a {}'.format(reason)
		self.put(buf)
		buf = b'stop\n'
		return self.proccess.communicate(input=buf)


