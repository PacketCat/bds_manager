import requests, os, subprocess
from bs4 import BeautifulSoup
import zipfile
import shutil

def check_server_updates(logger):
	version = None

	if not os.path.exists('./original'):
		os.mkdir('./original')
	if os.path.exists('./server.version'):
		with open('./server.version', 'r') as ver:
			version = ver.read()
	logger.info('main', 'Checking bds actual version...')
	soup = BeautifulSoup(requests.get('https://www.minecraft.net/en-us/download/server/bedrock').text, 'html.parser')
	link = soup.find(attrs={'data-platform': 'serverBedrockLinux'}).get('href')

	if link[len('https://minecraft.azureedge.net/bin-linux/bedrock-server-'):-4] != version:
		logger.info('main', 'Current version = {}, new version {} is available, downloading...'.format(version, link[len('https://minecraft.azureedge.net/bin-linux/bedrock-server-'):-4]))
		#if subprocess.call(['curl', link, '-s', '-o', './original/server_image']) != 0: raise Exception('e')
		cont = requests.get(link, stream = True)
		if cont.status_code != 200:
			logger.error('main', 'Download failed!')
			return -1
		with open('./original/server_image', 'wb') as tof:
			cont.raw.decode_content = True
			shutil.copyfileobj(cont.raw, tof)
		logger.info('main', 'Download complete.')
		with open('./server.version', 'w') as ver:
			ver.write(link[len('https://minecraft.azureedge.net/bin-linux/bedrock-server-'):-4])
			return 1
	else:
		logger.info('main', 'Server up-to-date.')
	return 0


def extract(logger, servername='Dedicated Server'):
	if not os.path.exists('./environ'):
		logger.info('main', 'Extracting server from image...')
		os.mkdir('./environ')
		with zipfile.ZipFile('./original/server_image', 'r') as zipp:
			zipp.extractall('./environ')
		proper = ''
		with open('./environ/server.properties', 'r') as prop:
			proper = prop.read()
		proper = proper.replace('level-name=Bedrock level', 'level-name=main')
		proper = proper.replace('server-name=Dedicated Server', 'server-name={}'.format(servername))
		with open('./environ/server.properties', 'w') as prop:
			prop.write(proper)
		logger.info('main', 'Extraction complete.')


	else:
		logger.info('main', 'Extracting server from image...')
		shutil.copyfile('./environ/server.properties', './backups/server.properties')
		shutil.copyfile('./environ/permissions.json', './backups/permissions.json')
		shutil.copyfile('./environ/whitelist.json', './backups/white_list.json')
		try:
			shutil.copytree('./environ/resourse_packs', './backups/.resourse_packs')
			shutil.copytree('./environ/behavior_packs', './backups/.behavior_packs')
		except:
			pass

		with zipfile.ZipFile('./original/server_image', 'r') as zipp:
			zipp.extractall('./environ')

		os.remove('./environ/server.properties')
		os.remove('./environ/permissions.json')
		os.remove('./environ/whitelist.json')
		shutil.copyfile('./backups/server.properties', './environ/server.properties')
		shutil.copyfile('./backups/permissions.json', './environ/permissions.json')
		shutil.copyfile('./backups/white_list.json', './environ/whitelist.json')

		try:
			shutil.rmtree('./environ/resourse_packs')
			shutil.rmtree('./environ/behavior_packs')
			shutil.movetree('./backups/.resourse_packs', './environ/resourse_packs')
			shutil.movetree('./backups/.behavior_packs', './environ/behavior_packs')
		except:
			pass

		logger.info('main', 'Extraction complete.')
	os.system('chmod +x ./environ/bedrock_server')
