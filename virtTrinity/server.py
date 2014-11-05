import os
import json
import result_manager
import pkg_resources
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from string import Template


class RequestHandler(BaseHTTPRequestHandler):
    # pylint: disable=E1101
    result_mgr = result_manager.ResultManager.Instance()

    def log_message(self, format, *args):
        return

    def do_GET(self):
        def load_file(file_name):
            return pkg_resources.resource_string(
                __name__, file_name)

        send_data = ''

        if self.path in ['/', '/stats']:
            mimetype = 'text/html'
            stat_content = load_file('data/html/stats.html')
            html_dict = {"content": stat_content}
            html_template = Template(load_file('data/html/main.html'))
            send_data = html_template.safe_substitute(html_dict)
        elif self.path == '/log':
            mimetype = 'text/html'
            log_content = load_file('data/html/log.html')
            html_dict = {"content": log_content}
            html_template = Template(load_file('data/html/main.html'))
            send_data = html_template.safe_substitute(html_dict)
        elif self.path.endswith('.js'):
            mimetype = 'application/javascript'
            file_name = os.path.join('data/js', self.path[1:])
            send_data = load_file(file_name)
        elif self.path.endswith('.css'):
            mimetype = 'text/css'
            file_name = os.path.join('data/css', self.path[1:])
            send_data = load_file(file_name)
        elif self.path.startswith('/json/log-'):
            log_idx = 0
            log_count = 0
            try:
                _, log_idx, log_count = self.path.split("-")
                log_idx = int(log_idx)
                log_count = int(log_count)
            except ValueError:
                pass

            mimetype = 'application/json'
            send_data = json.dumps(self.result_mgr.log(log_idx, log_count))
        elif self.path == '/json/stats':
            mimetype = 'application/json'
            send_data = json.dumps(self.result_mgr.stats())

        if send_data:
            self.send_response(200)
            self.send_header('Content-type', mimetype)
            self.end_headers()
            self.wfile.write(send_data)


class Server(HTTPServer):
    def __init__(self):
        HTTPServer.__init__(self, ("127.0.0.1", 8000), RequestHandler)
