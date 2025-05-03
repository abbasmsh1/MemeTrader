from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
from dataclasses import dataclass
from config.config import MIN_PURCHASE_AMOUNT

@dataclass
class Trade:
    timestamp: datetime
    symbol: str
    type: str  # 'buy' or 'sell'
    amount: float
    price: float
    total: float
    profit_loss: Optional[float] = None

class TestWallet:
    def __init__(self, initial_balance: float, target_balance: float):
        self.initial_balance = initial_balance
        self.target_balance = target_balance
        self.balance = initial_balance
        self.positions: Dict[str, Dict] = {}  # symbol -> {amount, entry_price}
        self.trade_history: List[Trade] = []
        self._initialized = False
    
    def initialize_with_btc(self, btc_price: float):
        """Initialize wallet with BTC purchase"""
        if not self._initialized and self.balance >= MIN_PURCHASE_AMOUNT:
            # Calculate amount of BTC to buy (50% of initial balance)
            btc_amount = (self.balance * 0.5) / btc_price
            self.balance -= btc_amount * btc_price
            self.positions['BTCUSDT'] = {
                'amount': btc_amount,
                'entry_price': btc_price
            }
            self.trade_history.append(Trade(
                timestamp=datetime.now(),
                symbol='BTCUSDT',
                type='buy',
                amount=btc_amount,
                price=btc_price,
                total=btc_amount * btc_price
            ))
            self._initialized = True
    
    def buy(self, symbol: str, amount: float, price: float) -> bool:
        """Execute a buy trade"""
        total_cost = amount * price
        
        # Enforce minimum purchase amount
        if total_cost < MIN_PURCHASE_AMOUNT:
            return False
            
        if total_cost > self.balance:
            return False
        
        self.balance -= total_cost
        if symbol in self.positions:
            # Average down
            current_position = self.positions[symbol]
            total_amount = current_position['amount'] + amount
            total_cost = (current_position['amount'] * current_position['entry_price']) + total_cost
            current_position['entry_price'] = total_cost / total_amount
            current_position['amount'] = total_amount
        else:
            self.positions[symbol] = {
                'amount': amount,
                'entry_price': price
            }
        
        self.trade_history.append(Trade(
            timestamp=datetime.now(),
            symbol=symbol,
            type='buy',
            amount=amount,
            price=price,
            total=total_cost
        ))
        return True
    
    def sell(self, symbol: str, amount: float, price: float) -> bool:
        """Execute a sell trade"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if amount > position['amount']:
            return False
        
        total_value = amount * price
        profit_loss = total_value - (amount * position['entry_price'])
        
        self.balance += total_value
        position['amount'] -= amount
        
        if position['amount'] == 0:
            del self.positions[symbol]
        
        self.trade_history.append(Trade(
            timestamp=datetime.now(),
            symbol=symbol,
            type='sell',
            amount=amount,
            price=price,
            total=total_value,
            profit_loss=profit_loss
        ))
        return True
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        total = self.balance
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total += position['amount'] * current_prices[symbol]
        return total
    
    def get_progress_to_target(self, current_prices: Dict[str, float]) -> float:
        """Calculate progress towards target balance"""
        current_value = self.get_total_value(current_prices)
        return ((current_value - self.initial_balance) / 
                (self.target_balance - self.initial_balance)) * 100
    
    def get_performance_summary(self) -> Dict:
        """Get trading performance summary"""
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for trade in self.trade_history 
                           if trade.profit_loss and trade.profit_loss > 0)
        total_profit_loss = sum(trade.profit_loss or 0 for trade in self.trade_history)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_profit_loss': total_profit_loss
        } 