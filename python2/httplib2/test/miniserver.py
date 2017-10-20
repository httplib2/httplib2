import logging
import os
import SimpleHTTPServer
import SocketServer
import threading

HERE = os.path.dirname(__file__)
logger = logging.getLogger(__name__)


class ThisDirHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = path.split('?', 1)[0].split('#', 1)[0]
        return os.path.join(HERE, *filter(None, path.split('/')))

    def log_message(self, s, *args):
        # output via logging so nose can catch it
        logger.info(s, *args)


def start_server(handler, use_tls=False):
    httpd = SocketServer.TCPServer(use_tls, ("", 0), handler)
    threading.Thread(target=httpd.serve_forever).start()
    _, port = httpd.socket.getsockname()
    return httpd, port
