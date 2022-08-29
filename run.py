import wsgiref.simple_server
import overlay
import config

with wsgiref.simple_server.make_server('', config.PORT, overlay.application) as httpd:
    print("Go to http://localhost:{}/".format(config.PORT))

    # Respond to requests until process is killed
    httpd.serve_forever()
