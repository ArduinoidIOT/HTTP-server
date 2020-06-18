from handlers import BaseHandler


class DFL_500_Handler(BaseHandler):
    def postprocess(self):
        self.set_header('Content-Length', "31")
        self.code = 500

    def send_data(self):
        self.socket.send(b"The server encountered an error")


class DFL_404_Handler(BaseHandler):
    def postprocess(self):
        self.set_header('Content-Length', "44")
        self.code = 404

    def send_data(self):
        self.socket.send(b"The page you are looking for cannot be found")


class DFL_501_Handler(BaseHandler):
    def postprocess(self):
        self.set_header('Content-Length', "43")
        self.code = 501

    def send_data(self):
        self.socket.send(b"The page you are looking is not implemented")
