import os
import jinja2

def function(api):	
	local_dir = os.path.dirname(__file__)
	template_path = os.path.join(local_dir, 'lastsub.j2')

	with open(template_path, "r") as file:
		template_bytes = file.read()
		
	env = jinja2.Environment()
	template = env.from_string(template_bytes)
	rendered_bytes = template.render(client_id=api.client_id, access_token=api.token['access_token'], account_id=api.token['sub']).encode("utf8")
	
	api.start_response('200 OK', [('Content-Type','text/html')])
	return [rendered_bytes]