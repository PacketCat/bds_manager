
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

	def __init__(self, levelname, log, backupinter):
		self.state = 0
		self.log = log
		self.last_backup = 0
		self.b_interval = backupinter
		self.levelname = levelname

		#Checking if world dir is not exists
		if not os.path.exists('./worlds/{}'.format(levelname)): 
			log.error('main', 'World folder not found >> trying create;')
			os.mkdir('./worlds/{}'.format(self.levelname))

		#Cheking if ./environ exists, if not -> exception bc in this dir must be server binary
		if not os.path.exists('./environ') or not os.path.exists('./environ/worlds'): 
			raise HandlerFatalException("Root directory is invalid, can't work here")

		self.state = 1

		#Copying world dir to ./environ/main
		log.info('main','Copying directory')
		shutil.copytree('./worlds/{}'.format(levelname), './environ/worlds/main')

		#Server launch
		self.proccess = Popen(['./bedrock_server'], cwd='./environ/', stdin=PIPE, stdout=PIPE)
		os.set_blocking(self.proccess.stdin.fileno(), False)

		log.info('main', 'Changing logging state: main >> server')


	def _check_b(self):
		#Checks last backup time, calls on every get/put operation
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
						zip.write(root +'/' + file, (root+'/'+file)[len('./environ/worlds/main/'):])
		self.log.info('server', 'Backup complete.')

	def get(self):
		self._check_b()
		return self.proccess.stdout.readline().decode()

	def put(self, data):
		self._check_b()
		buf = data.encode() + b'\n'
		return self.proccess.stdin.write(buf)


	def stop(self, reason = 'Server stopped'):
		self.log.info('server', 'Stopping server')
		self.log.info('server','Changing logging state: server >> main')

		buf = 'kick @a {}'.format(reason)
		self.put(buf) #Kicks players from server
		buf = b'stop\n'
		self.proccess.communicate(input=buf) #Stops server normally

		self.log.info('main', 'Cleaning...')
		self.state = 2

		#Moving ./environ/main to world folder
		shutil.rmtree('./worlds/{}'.format(self.levelname)) 
		shutil.copytree('./environ/worlds/main', './worlds/{}'.format(self.levelname))
		self.state = 1 
		shutil.rmtree('./environ/worlds/main')

		self.state = 0



	def recovfrom_backup(self, savepath):
		#Function to recovery from backup
		if not os.path.exists(savepath): return -1
		self.stop()
		with zipfile.ZipFile(savepath, 'r') as zip:
			self.log.info('main', 'Recovering from backup')
			self.state = 2
		
			shutil.rmtree('./worlds/{}'.format(self.levelname))
			zip.extractall('./worlds/{}'.format(self.levelname))
		self.__init__(self.levelname, self.log, self.b_interval)

	def recovery(self):
		#Recovery function
		if self.state == 0:
			return
		elif self.state == 1:
			try:
				shutil.rmtree('./environ/worlds/main')
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




