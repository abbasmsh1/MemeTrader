from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime, timedelta
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET

class BinanceWrapper:
    def __init__(self):
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        
    def get_historical_klines(self, symbol, interval, lookback_days=7):
        """Get historical klines (candlestick data) for a symbol"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)
            
            klines = self.client.get_historical_klines(
                symbol,
                interval,
                start_time.strftime("%d %b %Y %H:%M:%S"),
                end_time.strftime("%d %b %Y %H:%M:%S")
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert string values to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            return df
            
        except BinanceAPIException as e:
            print(f"Error fetching historical data: {e}")
            return None
            
    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Error fetching current price: {e}")
            return None
            
    def get_24h_stats(self, symbol):
        """Get 24-hour statistics for a symbol"""
        try:
            stats = self.client.get_ticker(symbol=symbol)
            return {
                'price_change': float(stats['priceChange']),
                'price_change_percent': float(stats['priceChangePercent']),
                'volume': float(stats['volume']),
                'quote_volume': float(stats['quoteVolume'])
            }
        except BinanceAPIException as e:
            print(f"Error fetching 24h stats: {e}")
            return None 