import os, time, shutil
import zipfile, logger
import json

VER = '0.0.1a'

class Database:
	def __init__(self, debug=False):
		
		self._create_dirs()
		self.log = logger.Logging(debug=debug)

		self.gamerules = {}

		self.mconf = {}
		self.execute_after_stop = []

		self.players_online = {}

		self.firststart = 0

		self.is_online = False

		self.log.info('main', 'Getting configs...')

		if os.path.exists('./conf.json'):
			with open('./conf.json', 'r') as confl:
				self.mconf = json.load(confl)

		else:
			self.firststart = 1

		if 'version' not in list(self.mconf.keys()):
			self.mconf['version'] = VER
		elif 'version' in list(self.mconf.keys()) and self.mconf['version'] != VER:
			self.mconf = {'version': VER}

		if 'serverconfig' not in list(self.mconf.keys()):
			self.mconf['serverconfig'] = {
			'servername': 'BDS',
			'current_world': '',
			'backup_interval': 0,
			'checkupdate_interval': 86400,
			'reboot_interval': 604800,
			'session_keys': [],
			'startup_action': '',
			'password': None
			}
			self.log.warning('main', 'Password not setted')

		if 'worlds' not in list(self.mconf.keys()):
			if not os.path.exists('./worlds/'):
				os.mkdir('./worlds')
				self.mconf['worlds'] = {}
			else:
				self.mconf['worlds'] = {}
				self.iterworlds()
		self._sync()

	def set_password(self, password):
		self.mconf['serverconfig']['password'] = password
		self._sync()
				
	def set_online(self, state):
		self.log.debug('main', 'set_online called with '+ str(state))
		self.is_online = state
		if not state:
			for i in self.execute_after_stop:
				i()

	def set_servername(self, newname):
		oldname = self.mconf['serverconfig']['servername']
		self.mconf['serverconfig']['servername'] = newname
		try:
			with open('./environ/server.properties', 'r') as propget:
				prop = propget.read()
				with open('./environ/server.properties', 'w') as propwri:
					propwri.write(prop.replace('server-name={}'.format(oldname), 'server-name={}'.format(newname)))
		except:
			self.log.debug('main', 'error_on_write_servername')

		self._sync()

	def set_backup_interval(self, interval):
		self.mconf['serverconfig']['backup_interval'] = interval
		self._sync()

	def set_checkupdate_interval(self, interval):
		self.mconf['serverconfig']['checkupdate_interval'] = interval
		self._sync()

	def set_reboot_interval(self, interval):
		self.mconf['serverconfig']['reboot_interval'] = interval
		self._sync()

	def set_startup_action(self, action):
		self.mconf['serverconfig']['startup_action'] = action
		self._sync()



	def iterworlds(self):
		self.log.debug('main', 'Storing worlds...')
		root, dirs, files = next(os.walk('./worlds/'))
		for i in dirs:
			if os.path.exists('./worlds/{}/levelname.txt'.format(i)):
				with open('./worlds/{}/levelname.txt'.format(i), 'r') as wname:
					levelname=wname.read()
			else:
				levelname=i
			self.mconf['worlds'][i] = {'levelname': levelname}
		self._sync()


	def _sync(self):
		self.log.debug('main', 'Writing to disk')
		with open('./conf.json', 'wb') as confl:
			json.dump(self.mconf, confl)

	def get_worlds(self):
		return self.mconf['worlds']

	def get_world_info(self, worldname):
		world = self.mconf['worlds'][worldname]

		if os.path.exists('./worlds/{}/world_resource_packs.json'.format(worldname)):
			with open('./worlds/{}/world_resource_packs.json'.format(worldname), 'r') as wrp:
				resources = json.load(wrp)
		else:
			resources = []

		if os.path.exists('./worlds/{}/world_behavior_packs.json'.format(worldname)):
			with open('./worlds/{}/world_behavior_packs.json'.format(worldname), 'r') as wbp:
				behaviors = json.load(wbp)
		else:
			behaviors = []

		# if os.path.exists('./worlds/{}/world_icon.jpeg'.format(worldname)):
		# 	with open('./worlds/{}/world_icon.jpeg.json'.format(worldname), 'rb') as wi:
		# 		pic = wi.read()
		# else:
		# 	pic = None

		ret = {worldname: {
		'world': world,
		'resources': resources,
		'behaviors': behaviors,
		'pic': None
		}}

		if worldname == self.mconf['serverconfig']['current_world']:
			ret['gamerules'] = self.gamerules

		return json.dumps(ret)

	def select_world(self, worldname):
		self.log.debug('main', 'World changed')
		self.mconf['serverconfig']['current_world'] = worldname
		self._sync()

	def import_world(self, zippath):
		self.log.debug('main', 'Importing {}...'.format(zippath))
		with zipfile.ZipFile(zippath, 'r') as zipp:
			dist = './worlds/{}'.format(zippath.split('/')[-1].split('.')[0])
			dirc = 1
			saved = 0
			try:
				os.mkdir(dist)
				zipp.extractall(dist)
			except:
				while not saved:
					try:
						os.mkdir(dist + ' ({})'.format(dirc))
						zipp.extractall(dist + ' ({})'.format(dirc))
						saved = 1
					except:
						dirc += 1
			if saved == 1:
				dist = dist + ' ({})'.format(dirc)
			os.mkdir('./backups/' + dist.split('/')[-1])


			with open(dist + '/levelname.txt', 'r') as ln:
				levelname = ln.read()

			if os.path.exists(dist+'/resource_packs'):
				root, dirs, files = next(os.walk(dist+'/resource_packs'))
				for i in dirs: 
					self._try_to_add_rpack(dist + './resource_packs/' + i)

			if os.path.exists(dist+'/behavior_packs'):
				root, dirs, files = next(os.walk(dist+'/behavior_packs'))
				for i in dirs: 
					self._try_to_add_bpack(dist + './behavior_packs/' + i)

			self.mconf['worlds'][zippath.split('/')[-1].split('.')[0]] = {
			'levelname': levelname
			}
			os.remove(zippath)
			self._sync()
			self.iterworlds()
			self.log.debug('main', 'Imported to {}'.format(dist))
			return dist

	def new_world(self, levelname):
		self.log.debug('main', 'Creating new world "{}"'.format(levelname))
		dirc = 0
		saved = 0
		while not saved:
			try:
				os.mkdir('./worlds/w{}'.format(dirc))
				saved = 1
			except:
				dirc+=1
		try:
			os.mkdir('./backups/w{}'.format(dirc))
		except:
			pass
		with open('./worlds/w{}/levelname.txt'.format(dirc), 'wb') as wln:
			wln.write(levelname.encode())
		self.mconf['worlds']['w{}'.format(dirc)] = {'levelname': levelname}
		self._sync()
		self.log.debug('main', 'w{} world was created successfully.'.format(dirc))
		return 'w{}'.format(dirc)

	def delete_world(self, worldname):
		self.log.debug('main', 'Deleting world "{}"...'.format(worldname))
		if self.mconf['serverconfig']['current_world'] == worldname and self.is_online:
			return -1
		elif self.mconf['serverconfig']['current_world'] == worldname:
			self.mconf['serverconfig']['current_world'] = ""
			shutil.rmtree('./worlds/{}'.format(worldname))
			shutil.rmtree('./backups/{}'.format(worldname))
			self.mconf['worlds'].pop(worldname)
			self.iterworlds()
			self._sync()
			self.log.debug('main', '{} was deleted successfully.'.format(worldname))
		else:
			shutil.rmtree('./worlds/{}'.format(worldname))
			shutil.rmtree('./backups/{}'.format(worldname))
			self.mconf['worlds'].pop(worldname)
			self.iterworlds()
			self._sync()
			self.log.debug('main', '{} was deleted successfully.'.format(worldname))

	def apply_to_world(self, world, type, packfolder):
		self.log.debug('main', 'Applying packs to world')
		if self.mconf['serverconfig']['current_world'] == world and self.is_online:
			self.execute_after_stop.append(lambda: self.apply_to_world(world, type, packfolder))
			return 1
		else:
			if type == 'r':
				resource_h = {'packs':[]}
				resources = []
				if os.path.exists('./worlds/' + world + '/world_resource_pack_history.json'):
					with open('./worlds/' + world + '/world_resource_pack_history.json', 'r') as wrph_r:
						resource_h = json.load(wrph_r)

				if os.path.exists('./worlds/' + world + '/world_resource_packs.json'):
					with open('./worlds/' + world + '/world_resource_packs.json', 'r') as wrp_r:
						resources = json.load(wrp_r)

				with open(packfolder + '/manifest.json', 'r') as manifest:
					man = json.load(manifest)

				history_add = {'can_be_redownloaded': False, 'name': man['header']['name'], 'uuid': man['header']['uuid'], 'version': man['header']['version']}
				if 'subpacks' in man['header'].keys():
					history_add['subpacks_count'] = len(man['header']['subpacks'])
				add = {
				'pack_id': man['header']['uuid'],
				'version': man['header']['version']
				}
				if history_add in resource_h['packs'] and add not in resources:
					resources.append(add)
					with open('./worlds/' + world + '/world_resource_packs.json', 'wb') as wr:
						json.dump(resources, wr)
				else:
					resource_h['packs'].append(history_add)
					resources.append(add)

					if not os.path.exists('./worlds/'+world+'/resource_packs/'):
						os.mkdir('./worlds/'+world+'/resource_packs/')

					if not os.path.exists('./worlds/{}/resource_packs/{}'.format(world, packfolder.split('/')[-1])):
						shutil.copytree(packfolder, './worlds/{}/resource_packs/{}'.format(world, packfolder.split('/')[-1]))

					with open('./worlds/' + world + '/world_resource_pack_history.json', 'wb') as wr:
						json.dump(resource_h, wr)
					with open('./worlds/' + world + '/world_resource_packs.json', 'wb') as wr:
						json.dump(resources, wr)

			elif type == 'b':
				resource_h = {'packs':[]}
				resources = []
				if os.path.exists('./worlds/' + world + '/world_behavior_pack_history.json'):
					with open('./worlds/' + world + '/world_behavior_pack_history.json', 'r') as wrph_r:
						resource_h = json.load(wrph_r)

				if os.path.exists('./worlds/' + world + '/world_behavior_packs.json'):
					with open('./worlds/' + world + '/world_behavior_packs.json', 'r') as wrp_r:
						resources = json.load(wrp_r)

				with open(packfolder + '/manifest.json', 'r') as manifest:
					man = json.load(manifest)

				history_add = {"can_be_redownloaded": False, "name": man['header']['name'], "uuid": man['header']['uuid'], "version": man['header']['version']}
				if 'subpacks' in man['header'].keys():
					history_add['subpacks_count'] = len(man['header']['subpacks'])
				add = {
				"pack_id": man['header']['uuid'],
				"version": man['header']['version']
				}
				if history_add in resource_h['packs'] and add in resources:
					resources.append(add)
					with open('./worlds/' + world + '/world_behavior_packs.json', 'wb') as wr:
						json.dump(resources, wr)
				else:
					resource_h['packs'].append(history_add)
					resources.append(add)

					if not os.path.exists('.worlds/'+world+'/behavior_packs/'):
						os.mkdir('./worlds/'+world+'/behavior_packs/')

					shutil.copytree(packfolder, './worlds/{}/behavior_packs/{}'.format(world, packfolder.split('/')[-1]))

					with open('./worlds/' + world + '/world_behavior_pack_history.json', 'wb') as wr:
						json.dump(resource_h, wr)
					with open('./worlds/' + world + '/world_behavior_packs.json', 'wb') as wr:
						json.dump(resources, wr)
			self.log.debug('main', 'Applied')

	def disapply_to_world(self, world, type, packuuid, packversion):
		self.log.debug('main', 'Discarding packs from world')
		if self.mconf['serverconfig']['current_world'] == world and self.is_online:
			self.execute_after_stop.append(lambda: self.disapply_to_world(world, type, packuuid, packversion))
			return 1
		else:
			if type == 'r':
				resources = []

				if os.path.exists('./worlds/' + world + '/world_resource_packs.json'):
					with open('./worlds/' + world + '/world_resource_packs.json', 'r') as wrp_r:
						resources = json.load(wrp_r)

				add = {
				'pack_id': packuuid,
				'version': packversion
				}
				
				resources.remove(add)

				with open('./worlds/' + world + '/world_resource_packs.json', 'wb') as wr:
					json.dump(resources, wr)

			if type == 'b':
				resources = []

				if os.path.exists('./worlds/' + world + '/world_behavior_packs.json'):
					with open('./worlds/' + world + '/world_behavior_packs.json', 'r') as wrp_r:
						resources = json.load(wrp_r)

				add = {
				'pack_id': packuuid,
				'version': packversion
				}
				
				resources.remove(add)

				with open('./worlds/' + world + '/world_behavior_packs.json', 'wb') as wr:
					json.dump(resources, wr)
		self.log.debug('main', 'Discarded')


	def import_mcpack(self, path):
		self.log.debug('main', 'Importing pack "{}"...'.format(path))
		with zipfile.ZipFile(path, 'r') as zz:
			print(zz.namelist())
			if 'manifest.json' not in zz.namelist(): return self.import_world(path)
			manifest = json.loads(zz.read('manifest.json').decode())
			if manifest['modules'][0]['type'] == 'resources':
				tmp = './.temp/' + str(time.time())
				os.mkdir(tmp)
				zz.extractall(tmp)
				self._try_to_add_rpack(tmp, name = path.split('/')[-1].split('.')[0])
				shutil.rmtree(tmp)
			elif manifest['modules'][0]['type'] == 'data':
				tmp = './.temp/' + str(time.time())
				os.mkdir(tmp)
				zz.extractall(tmp)
				self._try_to_add_bpack(tmp, name = path.split('/')[-1].split('.')[0])
				shutil.rmtree(tmp)
			os.remove(path)
			self.log.debug('main', 'Imported successfully.')

	def remove_pack(self, uuid, version):
		self.log.debug('main', 'Removing pack {}:{} ...'.format(uuid, version))
		with open('./environ/valid_known_packs.json', 'r') as vkp:
			packs = json.load(vkp)

			for i, v in enumerate(packs[1:]):
				if v['uuid'] == uuid and v['version'] == version:
					packs.pop(i+1)
					shutil.rmtree('./environ/'+v['path'])
		with open('./environ/valid_known_packs.json', 'wb') as vkp:
			json.dump(packs, vkp)
		self.log.debug('main', 'Removed successfully.')

	def list_rpacks(self):
		root, dirs, files = next(os.walk('./environ/resource_packs'))
		response = []
		for i in dirs:
			element = {"path": os.path.join(root, i)}
			with open(os.path.join(root, i, 'manifest.json'), 'r') as rd:
				manifest = json.load(rd)
				element['name'] = manifest['header']['name']
				element['uuid'] = manifest['header']['uuid']
				element['version'] = manifest['header']['version']
			response.append(element)
		return json.dumps(response)


	def list_bpacks(self):
		root, dirs, files = next(os.walk('./environ/behavior_packs'))
		response = []
		for i in dirs:
			element = {"path": os.path.join(root, i)}
			with open(os.path.join(root, i, 'manifest.json'), 'r') as rd:
				manifest = json.load(rd)
				element['name'] = manifest['header']['name']
				element['uuid'] = manifest['header']['uuid']
				element['version'] = manifest['header']['version']
			response.append(element)
		return json.dumps(response)





	def _try_to_add_rpack(self, path, name = None):
		vkn = None
		with open('./environ/valid_known_packs.json', 'r') as vkp:
			vkn = json.load(vkp)
		with open(path + '/manifest.json', 'r') as manifest:
			man = json.load(manifest)
		packs = {a['uuid']: a['version'] for a in vkn[1:]}
		print(packs)
		print(man['header']['uuid'])
		if man['header']['uuid'] not in packs.keys() or man['header']['uuid'] in packs.keys() and packs[man['header']['uuid']] != man['header']['version']: 
			if name:
				shutil.copytree(path, './environ/resource_packs/{}'.format(name))
			else:
				shutil.copytree(path, './environ/resource_packs/{}'.format(path.split('/')[-1]))
			with open('./environ/valid_known_packs.json', 'wb') as vkp:
				if name:
					vkn.append({
					"file_system" : "RawPath",
					"path" : "resource_packs/{}".format(name),
					"uuid" : man['header']['uuid'],
					"version" : '.'.join(map(str, man['header']['version']))
					})
				else:
					vkn.append({
						"file_system" : "RawPath",
						"path" : "resource_packs/{}".format(path.split('/')[-1]),
						"uuid" : man['header']['uuid'],
						"version" : '.'.join(map(str, man['header']['version']))
						})
				json.dump(vkn, vkp)
		return -1

	def _try_to_add_bpack(self, path, name = None):
		vkn = None
		with open('./environ/valid_known_packs.json', 'r') as vkp:
			vkn = json.load(vkp)
		with open(path + '/manifest.json', 'r') as manifest:
			man = json.load(manifest)
		packs = {a['uuid']: a['version'] for a in vkn[1:]}
		if man['header']['uuid'] not in packs.keys() or man['header']['uuid'] in packs.keys() and packs[man['header']['uuid']] != man['header']['version']: 
			if name:
				shutil.copytree(path, './environ/behavior_packs/{}'.format(name))
			else:
				shutil.copytree(path, './environ/behavior_packs/{}'.format(path.split('/')[-1]))
			
			with open('./environ/valid_known_packs', 'wb') as vkp:
				if name:
					vkn.append({
					"file_system" : "RawPath",
					"path" : "behavior_packs/{}".format(name),
					"uuid" : man['header']['uuid'],
					"version" : '.'.join(map(str, man['header']['version']))
					})
				else:
					vkn.append({
						"file_system" : "RawPath",
						"path" : "behavior_packs/{}".format(path.split('/')[-1]),
						"uuid" : man['header']['uuid'],
						"version" : '.'.join(map(str, man['header']['version']))
						})
				json.dump(vkn, vkp)
		return -1

	def _create_dirs(self):
		if not os.path.exists('./worlds'):
			os.mkdir('./worlds')
		if not os.path.exists('./logs'):
			os.mkdir('./logs')
		if not os.path.exists('./backups'):
			os.mkdir('./backups')
		if not os.path.exists('./.temp'):
			os.mkdir('./.temp')
