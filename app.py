import asyncio
import ccxt
import ccxt.async_support
import json
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import sys
from typing import List
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
            (r"/parallel/([^/]+)/([^/]+)", ParallelExchangeAPIHandler),
            (r"/parallel/method/fetch_order_books/([^/]+)", ParallelFetchOrderBooks),
        ]
        settings = dict(
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)

        self.exchanges = {}
        self.async_exchanges = {}

        apikeys = {}
        if options.apikeys != "":
            with open(options.apikeys, "r") as f:
                apikeys = yaml.load(f)
        self.apikeys = apikeys


def get_module(module:str):
    return sys.modules[module].__dict__


def get_ccxt_class(exchange:str):
    module = get_module("ccxt")
    if exchange not in module:
        raise ValueError("Invalid exchange %s" % exchange)
    return module[exchange]


def get_async_ccxt_class(exchange:str):
    module = get_module("ccxt.async_support")
    if exchange not in module:
        raise ValueError("Invalid exchange %s" % exchange)
    return module[exchange]


class HomeHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("hello world!")


class BaseHandler(tornado.web.RequestHandler):

    @property
    def exchanges(self):
        return self.application.exchanges

    def get_apikey(self, exchange):
        """Get apiKey and secret for an exchange. Returns empty dict if not available.
        """
        return self.application.apikeys.get(exchange, {})

    def get_ccxt_class(self, exchange:str):
        return get_ccxt_class(exchange)

    def get_exchange(self, exchange:str):
        if exchange not in self.exchanges:
            cls = self.get_ccxt_class(exchange)
            if options.nonce_msec:
                cls.nonce = lambda self: cls.milliseconds()
            apikey = self.get_apikey(exchange)
            self.exchanges[exchange] = cls(apikey)
        return self.exchanges[exchange]


class SyncBaseHandler(BaseHandler):
    pass


class AsyncBaseHandler(BaseHandler):

    @property
    def exchanges(self):
        return self.application.async_exchanges

    def get_ccxt_class(self, exchange:str):
        return get_async_ccxt_class(exchange)


class ExchangeAPIHandler(SyncBaseHandler):

    def post(self, exchange, method):
        ex = self.get_exchange(exchange)

        if len(self.request.body) > 0:
            request = json.loads(self.request.body)
        else:
            request = {}
        func = getattr(ex, method)
        result = func(**request)

        self.write(json.dumps(result))


async def parallel_run(async_callable, params:List[dict]):
    cors = [async_callable(**param) for param in params]
    results = await asyncio.gather(*cors)
    return results


class ParallelExchangeAPIHandler(AsyncBaseHandler):

    def post(self, name:str, method:str):
        request = json.loads(self.request.body)

        exchange = self.get_exchange(name)
        params = request
        async_callable = getattr(exchange, method)

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            parallel_run(async_callable, params)
        )
        self.write(json.dumps(results))


class ParallelFetchOrderBooks(AsyncBaseHandler):

    def post(self, name:str):
        exchange = self.get_exchange(name)

        request = json.loads(self.request.body)

        # TODO validation
        symbols = request["symbols"]
        params =[
            {"symbol":symbol, "params":request.get("params",{})} for symbol in symbols
        ]

        loop = asyncio.get_event_loop()
        order_books = loop.run_until_complete(
            parallel_run(exchange.fetch_order_book, params)
        )
        response = {
            symbol: order_book for symbol, order_book in zip(symbols, order_books)
        }
        return self.write(response)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

