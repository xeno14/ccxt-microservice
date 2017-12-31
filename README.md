ccxt-server
===========

Micro service to call cryptocurrency exchanges API using [ccxt](https://github.com/ccxt/ccxt).

1. Run a service

  ```
  python app.py
  ```
  or
  ```
  docker-compose up 
  ```

2. Send a request

  Send request to http://localhost:5000/*exchange*/*method*, for example, fetch ticker of bittrex for ETH/BTC:

  ```
  curl -H 'Content-Type:application/json' -d'{"symbol":"ETH/BTC"}' localhost:5000/bittrex/fetch_ticker
  ```
  
