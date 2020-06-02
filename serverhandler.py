
#Вроде рабочая версия

from subprocess import Popen, PIPE
import shutil
import os, time, zipfile



#Fatal exception class
class HandlerFatalException(Exception):
	def __init__(self, *args):
		if args:
			self.message = args[0]
		else:
			self.message = None
	def __str__(self):
		if not self.message:
			return "UNKNOWN ERROR OCCURRED"
		else:
			return "HandlerFatalException: {0}".format(self.message)












class Handler:

	def __init__(self, levelname, db, backupinter):
		self.state = 0
		self.log = db.log
		self.last_backup = 0
		self.b_interval = backupinter
		self.levelname = levelname
		self.db = db
		self.return_data = None
		self.server_started = False

		#Checking if world dir is not exists
		if not os.path.exists('./worlds/{}'.format(levelname)): 
			self.log.error('main', 'World folder not found >> trying create;')
			os.mkdir('./worlds/{}'.format(self.levelname))

		#Cheking if ./environ exists, if not -> exception bc in this dir must be server binary
		if not os.path.exists('./environ'): 
			raise HandlerFatalException("Root directory is invalid, can't work here")

		self.state = 1

		#Copying world dir to ./environ/main
		self.log.info('main','Moving directory')
		shutil.move('./worlds/{}'.format(levelname), './environ/worlds/main')

		#Server launch
		self.proccess = Popen(['./bedrock_server'], cwd='./environ/', stdin=PIPE, stdout=PIPE)
		os.set_blocking(self.proccess.stdin.fileno(), False)
		db.set_online(True)
		self.put('gamerule')

		self.log.info('main', 'Changing logging state: main >> server')


	def _check_b(self):
		#Checks last backup time, calls on every get/put operation
		if not self.b_interval:
			return
		if self.last_backup < time.time():
			self._backup()
			self.last_backup = int(time.time()) + self.b_interval

	def _backup(self):
		#Backup function
		self.log.info('server', 'Backuping...')

		#Checks if backup world folder, if not -> create it
		if not os.path.exists('./backups/'):
			raise HandlerFatalException("Root directory is invalid, can't work here")
		if not os.path.exists('./backups/{}'.format(self.levelname)):
			os.mkdir('./backups/{}'.format(self.levelname))
		
		#Dont backup if world dir empty, else backup
		if not os.listdir('./environ/worlds/main'):
			return
		else:
			with zipfile.ZipFile('./backups/{}/{}.zip'.format(self.levelname, time.time()), 'w') as zip:
				for root, dirs, files in os.walk('./environ/worlds/main/'):
					for file in files:
						if root.split('/')[-1] != 'db':
							continue
						zip.write(root +'/' + file, (root+'/'+file)[len('./environ/worlds/main/'):])
		self.log.info('server', 'Backup complete.')

	def get(self):
		self._check_b()
		ret = self.proccess.stdout.readline().decode()
		if '] Server started.\n' in ret:
			self.server_started = True
		return ret

	def put(self, data):
		self._check_b()
		buf = data.encode() + b'\n'
		self.proccess.stdin.write(buf)
		self.proccess.stdin.flush()


	def stop(self, reason = 'Server stopped'):
		self.log.info('server', 'Stopping server')
		self.log.info('server','Changing logging state: server >> main')

		for player in self.db.players_online: #Kicks players from server
			buf = 'kick {} {}'.format(player, reason)
			self.put(buf) 
		buf = b'stop\n'
		self.return_data = self.proccess.communicate(input=buf) #Stops server normally


		self.log.info('main', 'Cleaning...')
		self.state = 2

		#Moving ./environ/main to world folder
		shutil.move('./environ/worlds/main', './worlds/{}'.format(self.levelname))
		with open('./worlds/{}/levelname.txt'.format(self.levelname), 'w') as w:
			w.write(self.db.mconf['worlds'][self.levelname]['levelname'])
		self.state = 1 
		self.db.set_online(False)
		self.db.iterworlds()
		self.state = 0




	def recovfrom_backup(self, savepath):
		#Function to recovery from backup
		if not os.path.exists(savepath): return -1
		self.stop()
		with zipfile.ZipFile(savepath, 'r') as zip:
			self.log.info('main', 'Recovering from backup')
			self.state = 2
		
			zip.extractall('./worlds/{}'.format(self.levelname))
		self.__init__(self.levelname, self.log, self.b_interval)

	def recovery(self):
		#Recovery function
		if self.state == 0:
			return
		elif self.state == 1:
			try:
				shutil.move('./environ/worlds/main', './worlds/{}'.format(self.levelname))
			except:
				pass
		elif self.state == 2:
			if not os.path.exists('./worlds/{}'.format(self.levelname)):
				if not os.path.exists('./worlds/'):
					raise HandlerFatalException("Root directory is invalid, can't work here")
				os.mkdir('./worlds/{}'.format(self.levelname))

	def __del__(self):
		self.recovery()
		self.proccess.kill()




