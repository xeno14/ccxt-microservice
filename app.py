import ccxt
import json
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import sys

from tornado.options import define, options

define("port", default=5000, help="run on the given port", type=int)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/([^/]+)/([^/]+)", ExchangeAPIHandler),
        ]
        settings = dict(
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)

        self.exchanges = {}


class BaseHandler(tornado.web.RequestHandler):

    @property
    def exchanges(self):
        return self.application.exchanges


class HomeHandler(BaseHandler):

    def get(self):
        self.write(json.dumps({"test":1}))


def get_ccxt_class(exchange:str):
    cls_dict = sys.modules["ccxt"].__dict__
    if exchange not in cls_dict:
        raise ValueError("Invalid exchange %s" % exchange)
    return cls_dict[exchange]


class ExchangeAPIHandler(BaseHandler):

    def post(self, exchange, method):
        if exchange not in self.exchanges:
            cls = get_ccxt_class(exchange)
            self.exchanges[exchange] = cls()

        ex = self.exchanges[exchange]

        if len(self.request.body) > 0:
            request = json.loads(self.request.body)
        else:
            request = {}
        func = getattr(ex, method)
        result = func(**request)

        self.write(json.dumps(result))
    

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

