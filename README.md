ccxt-microservice
=================

Micro service to call cryptocurrency exchanges API using [ccxt](https://github.com/ccxt/ccxt).

# Usage

1. Run a service

  ```
  python app.py
  ```
  or
  ```
  docker-compose up 
  ```

2. Send a request

  Send post json to /*exchange*/*method*. Default port is 5000.

# Example

In ccxt, fetch ticker of Bittrex for ETH/BTc is:

```python
import ccxt

b = ccxt.bittrex()
result = b.fetch_ticker(symbol="ETH/BTC")
```

Following request is equivalent to the above.

```
curl -H 'Content-Type:application/json' -d'{"symbol":"ETH/BTC"}' localhost:5000/bittrex/fetch_ticker
```
  
