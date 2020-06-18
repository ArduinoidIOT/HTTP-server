from socket import socket, SOL_SOCKET, SO_REUSEADDR
from typing import Dict, Union, List, Tuple, Any, Optional, Pattern
from types import SimpleNamespace
import handlers
from HTTPRequestParser import Request
import re


class Server:
    urls: Dict[Pattern[str], Tuple[handlers.BaseHandler, Dict[Any, Any]]]
    conndata: Dict[socket, Union[None, Request]]

    def __init__(self, urls: List[Tuple[str, handlers.BaseHandler, Optional[Dict[Any, Any]]]],
                 port=10000, addr='127.0.0.1', settings=SimpleNamespace()):
        self._sock = socket()
        self._sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._sock.setblocking(False)
        self._sock.bind((addr, port))
        self._sock.listen()
        self.urls = {}
        for url in urls:
            url, handler = url[0], url[1:]
            if len(handler) == 1:
                handler = (handler[0], {})
            url = re.compile(f"^{url}$")
            self.urls[url] = handler
        self.deferred = []
        self.websockets = {}
        self.conndata = {}
        self.settings = settings
        self.requests_to_be_removed = []
        self.deferred_to_be_removed = []

    def _accept(self, sock):
        conn, addr = sock.accept()  # Should be ready
        conn.setblocking(False)
        self.conndata[conn] = Request(addr=addr)

    def _read(self, sock):
        try:
            data = sock.recv(1000)  # Should be ready
        except (ConnectionResetError, BrokenPipeError):
            self.requests_to_be_removed.append(sock)
            return
        if data:
            try:
                self.conndata[sock].update(data)
            except:
                sock.send(b"400 Bad Request\r\n\r\n")
            if self.conndata[sock].data_ready:
                self._handle_request(sock, self.conndata[sock])
        else:
            self.requests_to_be_removed.append(sock)
            sock.close()

    def _mainloop(self):
        try:
            self._accept(self._sock)
        except BlockingIOError:
            pass
        for sock in self.conndata:
            try:
                self._read(sock)
            except BlockingIOError:
                pass
        while len(self.requests_to_be_removed) > 0:
            del self.conndata[self.requests_to_be_removed.pop()]
        deferred: handlers.BaseHandler
        for deferred in self.deferred:
            if not deferred.defer_condition():
                deferred.postprocess()
                deferred.dump_response()
                deferred.cleanup()
                self.deferred_to_be_removed.append(deferred)
        while len(self.deferred_to_be_removed) > 0:
            self.deferred.remove(self.deferred_to_be_removed.pop())

    def _handle_request(self, sock: socket, request: Request):
        for url in self.urls:
            if not url.match(request.path):
                continue
            handler_args = self.urls[url]
            handler = handler_args[0](request, sock, handler_args[1])
            handler.preprocess()
            if not handler.defer_condition():
                handler.postprocess()
                handler.dump_response()
                if hasattr(handler, 'websocket'):
                    self.websockets[sock] = handler
                else:
                    handler.cleanup()
                    sock.close()
            else:
                self.deferred.append(request)
            self.requests_to_be_removed.append(sock)

    def run(self):
        while True:
            self._mainloop()
