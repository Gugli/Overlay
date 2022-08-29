import os
import importlib.util
import traceback
import urllib.request
import json
import config

local_dir = os.path.dirname(__file__)
token_path = os.path.join(local_dir, 'token.txt')
	
def token_get(env, start_response, errorlog):
	access_token = None
	if os.path.exists(token_path):
		with open(token_path, "rt") as tokenfile:
			line = tokenfile.read().strip()
			access_token = line if len(line) > 0 else None
	
	full_token = None
	if access_token != None:
		# check token validity
		request = urllib.request.Request('https://id.twitch.tv/oauth2/userinfo', headers={'Authorization' : 'Bearer ' + access_token} )
		with urllib.request.urlopen(request) as response:
			full_token = json.loads(response.read())
			full_token.update( {'access_token': access_token} )
		
	if full_token == None:
		# Get token
		url = 'https://id.twitch.tv/oauth2/authorize?client_id=' + config.CLIENT_ID + '&redirect_uri=' + config.REDIRECT_URL + '&response_type=token&scope=channel:read:subscriptions'
		start_response('307 Temporary Redirect', [('Location', url)])
		return (None, [])
		
	return (full_token, None)
	
def token_set(env, start_response, errorlog):
	if len(env['QUERY_STRING']) == 0 :
		start_response('200 OK', [('Content-Type','text/html')])
		return [b'<html><script>function init(){\n'
		 + b'var urlParams = new URLSearchParams(window.location.hash.substr(1));\n'
		 + b'var access_token = urlParams.get("access_token");\n'
		 + b'var Http = new XMLHttpRequest();\n'	 
		 + b'Http.open("GET", "/token?access_token="+access_token);\n' 
		 + b'Http.send(null);\n'	 
		 + b'Http.onreadystatechange = function(){\n'
		 + b'\tif ( (Http.readyState == 4) && (Http.status == 200) ) { window.location="/";}\n'
		 + b'}\n'	
		 + b'}</script><meta charset="UTF-8"><body onload="init()"></body></html>'
		]
	else :
		query = env['QUERY_STRING']		
		if query.startswith('access_token='):		
			token = query[13:]
			with open(token_path, "wt") as tokenfile:
				tokenfile.write(token.strip())
				
			start_response('307 Temporary Redirect', [('Location', '/')])
			return []
		else:
			start_response('501 Server Error', [])
			return []
		
def list_modules():
	modules_dir = os.path.join(local_dir, 'modules')
	modules = []
	for root, dirs, files in os.walk(modules_dir):
		for filename in files:
			(name, ext) = os.path.splitext(filename)
			if(ext == '.py'):
				path = os.path.join(root, filename)
				spec = importlib.util.spec_from_file_location(name,path)
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				modules.append({'name' : name, 'function' : module.function })
	return modules

class API:
	env				= None
	start_response	= None
	errorlog		= None
	token			= None
	modules			= None
	client_id		= None
	
	def __init__(self, env, start_response, errorlog, token, modules, client_id):
		self.env				= env
		self.start_response		= start_response
		self.errorlog			= errorlog
		self.token				= token
		self.modules			= modules
		self.client_id			= client_id
	
	
	
def do_index(api):
	api.start_response('200 OK', [('Content-Type','text/html')])
	index = [ ('<a href="./' + m['name'] + '">'+ m['name'] + '</a><br/>').encode('utf8') for m in api.modules]
	return [b'<head><title>Overlay</title></head><body>'] + index + [	b'</body>']


def application(env, start_response):

	errorlog = env['wsgi.errors'] if 'wsgi.errors' in env else None
	path = env['PATH_INFO']
	modules = list_modules()
	
	valid_paths = {
		'/': do_index,
	}
	for module in modules:
		valid_paths.update( {'/'+module['name'] : module['function'] } )
	
	try:
		if path == '/token':
			return token_set(env, start_response, errorlog)
		elif path in valid_paths:
			(token, r) = token_get(env, start_response, errorlog)
			if token == None: return r
			api = API(env, start_response, errorlog, token, modules, config.CLIENT_ID)
			return valid_paths[path](api)
		else:
			start_response('404 Not Found', [('Content-Type','text/plain')])
			return ["404 Not Found {}".format(path).encode("utf-8")]
		
	except Exception as e:
		start_response('500 Internal server error', [('Content-Type','text/plain')])
		if errorlog != None:
			print("Exception", file=errorlog)
			traceback.print_exc(file=errorlog)
		return [b'500 Internal server error']
		