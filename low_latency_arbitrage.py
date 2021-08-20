
import asyncio
import websockets
import json
import time
import hmac
import hashlib
import uvloop 

API_SECRET = 'your_api_secret_key'
API_KEY = 'your_api_key'

SYMBOL_1 = {#buy
        'symbol': 'tETHUSD',
        'ticker_bid': None,
        'ticker_ask': None
    }

SYMBOL_2 = {#sell
        'symbol': 'tETHBTC',
        'ticker_bid': None,
        'ticker_ask': None
    }

SYMBOL_3 = {#sell
        'symbol': 'tBTCUSD',
        'ticker_bid': None,
        'ticker_ask': None
    }


bitfinex_fees = 0.002
breakout_profit = 0

websocket_timeout = 17
loop_timer_ticker = 1E-10
loop_timer_arbitrage = 1E-10 # consuming CPU

amount_USD = 10001 


############################## get_ticker
async def get_ticker(symbol):
    
    SUB_MESG_TICKER = {
        'event': 'subscribe',
        'channel': 'ticker',
        'symbol': symbol['symbol']
    }
    
    async with websockets.connect('wss://api.bitfinex.com/ws/2') as websocket_get_ticker:
        await websocket_get_ticker.send(json.dumps(SUB_MESG_TICKER))
        
        while True:
            
            try:
                res = await asyncio.wait_for(websocket_get_ticker.recv(), timeout = websocket_timeout)
               
            except asyncio.TimeoutError:
                print('{0} -> in get_ticker() Waited {1}s, still to wait {2}s before disconnect'.format(symbol['symbol'], websocket_timeout, websocket_timeout))
                # No data in websocket_timeout seconds, check the connection.
                try:
                    pong_waiter = await websocket_get_ticker.ping()
                    await asyncio.wait_for(pong_waiter, timeout = websocket_timeout)
                except asyncio.TimeoutError:
                    # No response to ping in X seconds, disconnect.
                    print('{0} -> CONNECTION CLOSED raised exception in get_ticker() -> TRYING TO RECONNECT !!!'.format(symbol['symbol']))

                    raise websockets.ConnectionClosed('ConnectionClosed ---> in get_ticker()')
                    break
            else:
                
                ticker = json.loads(res)
                
                if ticker:
                    if isinstance(ticker, list):
                        if isinstance(ticker[1], list):                                                      
                            symbol['ticker_bid'] = ticker[1][0]
                            symbol['ticker_ask'] = ticker[1][2]

            await asyncio.sleep(loop_timer_ticker) 

        
############################## arbitrage
async def arbitrage():

    profit = -1
    
    global amount_USD
    
    nonce = str(int(round(time.time() * 1000)))
    
    auth_payload = 'AUTH{}'.format(nonce)
    signature = hmac.new(
      API_SECRET.encode(),
      msg = auth_payload.encode(),
      digestmod = hashlib.sha384
    ).hexdigest()
        
    PAYLOAD = {
      'apiKey': API_KEY,
      'event': 'auth',
      'authPayload': auth_payload,
      'authNonce': nonce,
      'authSig': signature,
      'filter': ['trading-' + SYMBOL_1['symbol'], 'trading-' + SYMBOL_2['symbol'], 'trading-' + SYMBOL_3['symbol']] 
    }
    
    async with websockets.connect('wss://api.bitfinex.com/ws/2') as websocket_arbitrage:
        await websocket_arbitrage.send(json.dumps(PAYLOAD))
    
        while True:

            #start = time.time()
            
            if(SYMBOL_1['ticker_ask'] and SYMBOL_2['ticker_bid'] and SYMBOL_3['ticker_bid']):
                
                # discount fees you get from bitfinex (depends on how many LEO & USD you have in your bitfinex wallet)
                # at the time of publishing this code, bitfinex conditions are as follow
                
                # > 10000 USDT LEO equiv + up to 6bps_fees = bitfinex_fees - (bitfinex_fees*0.25)
                crypto_crypto_bitfinex_fees = bitfinex_fees - (bitfinex_fees*0.15 + bitfinex_fees*0.15*0.25 + bitfinex_fees*0.15*0.25*0.25)
                crypto_fiat_bitfinex_fees = crypto_crypto_bitfinex_fees
                
                # > 5000 USDT LEO equiv
                #crypto_fiat_bitfinex_fees = bitfinex_fees
                #crypto_crypto_bitfinex_fees = bitfinex_fees - (bitfinex_fees*0.15 + bitfinex_fees*0.15*0.25)
                
                # > 1 USDT LEO equiv
                #crypto_fiat_bitfinex_fees = bitfinex_fees
                #crypto_crypto_bitfinex_fees = bitfinex_fees - (bitfinex_fees*0.15)
                
                step_1 = (amount_USD / float(SYMBOL_1['ticker_ask'])) * (1 - crypto_fiat_bitfinex_fees)                
                step_2 = (step_1 * float(SYMBOL_2['ticker_bid'])) * (1 - crypto_crypto_bitfinex_fees)                
                step_3 = (step_2 * float(SYMBOL_3['ticker_bid'])) * (1 - crypto_fiat_bitfinex_fees)

                profit = step_3 - amount_USD                
                
                if(profit > breakout_profit):
                    print('----> Profit Detected: {0}'.format(profit))
                    # Launch here your order routing (FIX or API) - buy SYMBOL_1, then sell SYMBOL_2, and finish by selling SYMBOL_3
                    profit = -1

            await asyncio.sleep(loop_timer_arbitrage)
            #duration = time.time() - start
            #print('--------> duration: ', duration)


tasks = [get_ticker(SYMBOL_1), get_ticker(SYMBOL_2), get_ticker(SYMBOL_3), arbitrage()]
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
    
try:
    loop.run_until_complete(asyncio.gather(*tasks))
except Exception as e:
    print('\n')
    print('ARBITRAGE EXCEPTION RAISED: {0}'.format(e))

