import os

def function(api):	
	local_dir = os.path.dirname(__file__)
	template_path = os.path.join(local_dir, 'date.htm')

	with open(template_path, "rb") as file:
		template_bytes = file.read()
		
	api.start_response('200 OK', [('Content-Type','text/html')])
	return [template_bytes]