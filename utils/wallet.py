from datetime import datetime
from config.config import INITIAL_BALANCE, TARGET_BALANCE

class SimulatedWallet:
    def __init__(self):
        self.balance = INITIAL_BALANCE
        self.positions = {}  # symbol -> {'amount': float, 'entry_price': float}
        self.trade_history = []
        self.target_balance = TARGET_BALANCE
        
    def can_open_position(self, symbol, amount, price):
        """Check if we can open a new position"""
        cost = amount * price
        return cost <= self.balance
        
    def open_position(self, symbol, amount, price):
        """Open a new position"""
        if not self.can_open_position(symbol, amount, price):
            return False
            
        cost = amount * price
        self.balance -= cost
        self.positions[symbol] = {
            'amount': amount,
            'entry_price': price
        }
        
        self.trade_history.append({
            'timestamp': datetime.now(),
            'type': 'OPEN',
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'cost': cost
        })
        
        return True
        
    def close_position(self, symbol, price):
        """Close an existing position"""
        if symbol not in self.positions:
            return False
            
        position = self.positions[symbol]
        amount = position['amount']
        value = amount * price
        
        self.balance += value
        profit = value - (amount * position['entry_price'])
        
        self.trade_history.append({
            'timestamp': datetime.now(),
            'type': 'CLOSE',
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'value': value,
            'profit': profit
        })
        
        del self.positions[symbol]
        return True
        
    def get_position_value(self, symbol, current_price):
        """Get current value of a position"""
        if symbol not in self.positions:
            return 0
            
        position = self.positions[symbol]
        return position['amount'] * current_price
        
    def get_total_value(self, current_prices):
        """Get total portfolio value including cash and positions"""
        total = self.balance
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total += self.get_position_value(symbol, current_prices[symbol])
                
        return total
        
    def get_progress_to_target(self, current_prices):
        """Get progress towards target balance as a percentage"""
        current_value = self.get_total_value(current_prices)
        progress = ((current_value - INITIAL_BALANCE) / 
                   (TARGET_BALANCE - INITIAL_BALANCE)) * 100
        return min(max(progress, 0), 100)  # Clamp between 0 and 100 