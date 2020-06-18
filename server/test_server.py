from handlers import *
from Server import Server


class HomeHandler(RequestHandler):
    def postprocess(self):
        self.set_data('Hello world')


server = Server([('/', HomeHandler)])

if __name__ == '__main__':
    server.run()
