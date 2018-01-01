import ccxt
import json
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import sys
import yaml

from tornado.options import define, options


define("port", default=5000, help="run on the given port", type=int)
define("apikeys", default="", help="apiKeys and secrets.", type=str)
define("nonce_msec", default=False, help="use milliseconds as nonce.", type=bool)


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

        apikeys = {}
        if options.apikeys != "":
            with open(options.apikeys, "r") as f:
                apikeys = yaml.load(f)
        self.apikeys = apikeys


class BaseHandler(tornado.web.RequestHandler):

    @property
    def exchanges(self):
        return self.application.exchanges

    def get_apikey(self, exchange):
        """Get apiKey and secret for an exchange. Returns empty dict if not available.
        """
        return self.application.apikeys.get(exchange, {})


class HomeHandler(BaseHandler):

    def get(self):
        self.write(json.dumps({"test":1}))


def get_ccxt_module():
    return sys.modules["ccxt"].__dict__


def get_ccxt_class(exchange:str):
    module = get_ccxt_module()
    if exchange not in module:
        raise ValueError("Invalid exchange %s" % exchange)
    return module[exchange]


class ExchangeAPIHandler(BaseHandler):

    def post(self, exchange, method):
        if exchange not in self.exchanges:
            cls = get_ccxt_class(exchange)

            # nonce override
            if options.nonce_msec:
                cls.nonce = lambda self: cls.milliseconds()

            apikey= self.get_apikey(exchange)
            self.exchanges[exchange] = cls(apikey)

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

