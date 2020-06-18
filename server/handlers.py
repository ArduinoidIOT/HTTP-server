from socket import socket
from HTTPRequestParser import Request
from typing import Union
from base64 import b64encode
from hashlib import sha1

http_codes = {
    100: 'Continue', 101: 'Switching Protocols', 200: "OK", 201: "Created", 202: "Accepted",
    203: "Non-Authorititative Information", 204: "No Content", 205: "Reset Content", 206: "Partial Content",
    300: "Multiple Choices", 301: "Moved Permanently", 302: "Found", 303: "See Other", 304: "Not Modified",
    307: "Temporary Redirect", 308: "Permanent Redirect", 400: "Bad Request", 401: "Unauthorized",
    402: "Payment Required", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed", 406: "Not Acceptable",
    407: "Proxy Authentication Required", 408: "Request Timeout", 409: "Conflict", 410: "Gone", 411: "Length Required",
    412: "Precondition Failed", 413: "Payload Too Large", 414: "URI Too Long", 415: "Unsupported Media Type",
    416: "Range Not Satisfiable", 417: "Expectation Failed", 418: "I'm a teapot", 422: "Unprocessable Entity",
    425: "Too Early", 426: "Upgrade Required", 428: "Precondition Required", 429: "Too Many Requests",
    431: "Request Header Fields Too Large", 451: "Unavailable For Legal Reasons", 500: "Internal Server Error",
    501: "Not Implemented", 502: "Bad Gateway", 503: "Service Unavailable", 504: "Gateway Timeout",
    505: "HTTP Version Not Supported", 506: "Variant Also Negotiates", 507: "Insufficient Storage",
    508: "Loop Detected", 510: "Not Extended", 511: "Network Authentication Required"
}


class BaseHandler:
    def __init__(self, request: Request, sock: socket, *args, **kwargs):
        self.request = request
        self.headers = {}
        self.code = 200
        self.data = b''
        self.dumped = False
        self.socket = sock
        self.initialize(*args, **kwargs)

    def initialize(self, *args, **kwargs):
        """The initialization function
            Write db initializations here, etc
        """
        pass

    def preprocess(self):
        """Handler to be run before request"""
        pass

    def postprocess(self):
        """Handler to be run after request"""
        pass

    def defer_condition(self):
        """Used to defer a request till the condition is fulfilled
            Useful for ratelimiting without blocking"""
        return False

    def set_header(self, header, val):
        """ Set headers here """
        self.headers[header] = [val]

    def add_header(self, header, val: Union[str, bytes]):
        if hasattr(val, 'decode'):
            val = val.decode()
        try:
            self.headers[header].append(val)
        except KeyError:
            self.set_header(header, val)

    def set_status_code(self, code):
        self.code = code

    def set_data(self, data: str):
        if hasattr(data, 'encode'):
            data = data.encode()
        self.data = data
        self.set_header('Content-Length', str(len(data)))

    def send_data(self):
        self.socket.send(self.data)

    def dump_response(self, close=True):
        """ WARNING: DO NOT OVERRIDE """
        try:
            self.dumped = True
            self.socket.send(b"HTTP/1.1 ")
            self.socket.send(str(self.code).encode())
            self.socket.send(b' ')
            self.socket.send(http_codes[self.code].encode())
            self.socket.send(b'\r\n')
            for header, values in self.headers.items():
                for value in values:
                    self.socket.send(header.encode())
                    self.socket.send(b": ")
                    self.socket.send(value.encode())
                    self.socket.send(b'\r\n')
            self.socket.send(b'\r\n')
            self.send_data()
            if close:
                self.socket.close()
        except BrokenPipeError:
            pass

    def cleanup(self):
        pass

    def redirect(self, location, permanent=False):
        self.code = 301 if permanent else 302
        self.set_header('Location', location)


class RequestHandler(BaseHandler):
    pass


class MonoStaticHandler(BaseHandler):
    def __init__(self, request, sock: socket, *args, **kwargs):
        super().__init__(request, sock, *args, **kwargs)
        self.static = kwargs['static']

    def send_data(self):
        with open(self.static, 'rb') as static_file:
            data = static_file.read(512)
            while data:
                self.socket.send(data)
                data = static_file.read(512)


class RedirectHandler(BaseHandler):
    def __init__(self, request, sock: socket, location, permanent=False, *args, **kwargs):
        super().__init__(request, sock, *args, **kwargs)
        self.redirect(location, permanent)


class WebSocketHandler(BaseHandler):
    def __init__(self, request: Request, sock: socket, *args, **kwargs):
        super().__init__(request, sock, *args, **kwargs)
        self.code = 101
        self.buffered_messages = b''
        self.websocket = True

    def initialize(self, *args, **kwargs):
        pass

    def accept(self):
        if 'upgrade' not in [val.lower() for val in self.request.headers.get(
                'Connection')] or self.request.method != 'GET' or '13' not in self.request.headers.get(
                'Sec-Websocket-Version') or self.request.headers.get('Sec-Websocket-Key') is None:
            self.reject(400)
        self.code = 101
        self.set_header('Sec-Websocket-Accept', b64encode(
            sha1(self.request.headers.get('Sec-Websocket-Key')[0] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")))
        self.set_header('Connection', 'upgrade')
        self.set_header('Upgrade', 'websocket')
        self.dump_response()

    def on_message(self, message):
        """ Message handler """
        pass

    def mainloop(self):
        """Main loop"""
        pass

    def reject(self, code):
        self.code = code
        self.dump_response(True)

    def dump_response(self, close=False):
        """ WARNING: DO NOT OVERRIDE """
        super().dump_response(close)
