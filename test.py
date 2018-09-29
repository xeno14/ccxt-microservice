import requests
import json


TARGET = "http://localhost:5000"


def post(endpoint, data):
    return requests.post(TARGET + endpoint, json.dumps(data))


def test_fetch_ticker():
    response = post("/bittrex/fetch_ticker", {"symbol": "ETH/BTC"})
    assert(response.status_code == 200)


def test_parallel_fetch_ticker():
    response = post("/parallel/bittrex/fetch_ticker", [{"symbol": "ETH/BTC"}, {"symbol": "BCH/BTC"}])
    assert(response.status_code == 200)


def main():
    test_fetch_ticker()
    test_parallel_fetch_ticker()


if __name__ == '__main__':
    main()
