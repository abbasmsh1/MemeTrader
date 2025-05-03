import json
import os
from typing import Dict, List, TypedDict
from datetime import datetime
from agents.trading_agents import MarketState

class TradingState(TypedDict):
    """Complete trading state including all agent outputs and wallet state"""
    current_prices: Dict[str, float]
    portfolio_value: float
    progress_to_target: float
    positions: Dict[str, Dict]
    available_balance: float
    market_analysis: str
    risk_assessment: str
    financial_advice: str
    risk_analysis: str
    trading_plan: str
    executed_trades: List[Dict]
    strategy: str
    last_updated: str

class StateManager:
    def __init__(self, state_file: str = "trading_state.json"):
        self.state_file = state_file
        self.states: Dict[str, TradingState] = {}
    
    def save_state(self, strategy: str, state: MarketState) -> None:
        """Save the trading state for a specific strategy"""
        # Convert state to TradingState format
        trading_state: TradingState = {
            'current_prices': state['current_prices'],
            'portfolio_value': state['portfolio_value'],
            'progress_to_target': state['progress_to_target'],
            'positions': state['positions'],
            'available_balance': state['available_balance'],
            'market_analysis': state.get('market_analysis', ''),
            'risk_assessment': state.get('risk_assessment', ''),
            'financial_advice': state.get('financial_advice', ''),
            'risk_analysis': state.get('risk_analysis', ''),
            'trading_plan': state.get('trading_plan', ''),
            'executed_trades': state.get('executed_trades', []),
            'strategy': strategy,
            'last_updated': datetime.now().isoformat()
        }
        
        # Update states dictionary
        self.states[strategy] = trading_state
        
        # Save to file
        with open(self.state_file, 'w') as f:
            json.dump(self.states, f, indent=2)
    
    def load_state(self, strategy: str) -> TradingState:
        """Load the trading state for a specific strategy"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.states = json.load(f)
        
        return self.states.get(strategy, {})
    
    def get_all_states(self) -> Dict[str, TradingState]:
        """Get all saved trading states"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.states = json.load(f)
        return self.states
    
    def clear_state(self, strategy: str = None) -> None:
        """Clear trading state for a specific strategy or all strategies"""
        if strategy:
            if strategy in self.states:
                del self.states[strategy]
        else:
            self.states = {}
        
        # Save updated states
        with open(self.state_file, 'w') as f:
            json.dump(self.states, f, indent=2) 