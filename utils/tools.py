from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from utils.binance_utils import BinanceWrapper

class HistoricalKlinesTool(BaseModel):
    """Tool for getting historical candlestick data"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "Get Historical Klines"
    description: str = "Get historical candlestick data for a cryptocurrency symbol"
    binance: BinanceWrapper = Field(default=None, exclude=True)
    
    def run(self, symbol: str, interval: str = "1h", lookback_days: int = 30) -> Optional[Dict[str, Any]]:
        df = self.binance.get_historical_klines(symbol, interval, lookback_days)
        if df is not None:
            return df.to_dict()
        return None

class CurrentPriceTool(BaseModel):
    """Tool for getting current price data"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "Get Current Price"
    description: str = "Get the current price for a cryptocurrency symbol"
    binance: BinanceWrapper = Field(default=None, exclude=True)
    
    def run(self, symbol: str) -> Optional[float]:
        return self.binance.get_current_price(symbol)

class Stats24hTool(BaseModel):
    """Tool for getting 24-hour statistics"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "Get 24h Statistics"
    description: str = "Get 24-hour trading statistics for a cryptocurrency symbol"
    binance: BinanceWrapper = Field(default=None, exclude=True)
    
    def run(self, symbol: str) -> Optional[Dict[str, float]]:
        return self.binance.get_24h_stats(symbol) 