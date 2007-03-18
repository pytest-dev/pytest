import BaseHTTPServer
from py.__.green import greensock2
from py.__.green.pipe.gsocket import GreenSocket


class GreenMixIn:
    """Mix-in class to handle each request in a new greenlet."""

    def process_request_greenlet(self, request, client_address):
        """Same as in BaseServer but as a greenlet.
        In addition, exception handling is done here.
        """
        try:
            self.finish_request(request, client_address)
            self.close_request(request)
        except:
            self.handle_error(request, client_address)
            self.close_request(request)

    def process_request(self, request, client_address):
        """Start a new greenlet to process the request."""
        greensock2.autogreenlet(self.process_request_greenlet,
                                request, client_address)


class GreenHTTPServer(GreenMixIn, BaseHTTPServer.HTTPServer):
    protocol_version = "HTTP/1.1"

    def server_bind(self):
        self.socket = GreenSocket.fromsocket(self.socket)
        BaseHTTPServer.HTTPServer.server_bind(self)


def test_simple(handler_class=None):
    if handler_class is None:
        from SimpleHTTPServer import SimpleHTTPRequestHandler
        handler_class = SimpleHTTPRequestHandler
    server_address = ('', 8000)
    httpd = GreenHTTPServer(server_address, handler_class)
    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()
