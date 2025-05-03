import json
import os
import shutil
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
        self.backup_file = f"{state_file}.backup"
        self.states: Dict[str, TradingState] = {}
        self._load_states()
    
    def _backup_state_file(self) -> None:
        """Create a backup of the current state file"""
        if os.path.exists(self.state_file):
            try:
                shutil.copy2(self.state_file, self.backup_file)
                print(f"Created backup of state file at {self.backup_file}")
            except Exception as e:
                print(f"Error creating backup: {str(e)}")
    
    def _load_states(self) -> None:
        """Load states from file with error handling"""
        if not os.path.exists(self.state_file):
            return
        
        try:
            # First, try to read and parse the file
            with open(self.state_file, 'r') as f:
                content = f.read().strip()
                if not content:  # Empty file
                    return
                
                try:
                    # Try to parse the JSON
                    self.states = json.loads(content)
                    return  # Successfully loaded states
                except json.JSONDecodeError as e:
                    print(f"Error parsing state file: {str(e)}")
                    print("Creating backup and starting fresh...")
                    
                    # Create backup of corrupted file
                    self._backup_state_file()
                    
                    # Start fresh with empty states
                    self.states = {}
                    self._save_states()
                    
        except Exception as e:
            print(f"Error loading state file: {str(e)}")
            self.states = {}
    
    def _save_states(self) -> None:
        """Save states to file with error handling"""
        try:
            # Create a temporary file first
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(self.states, f, indent=2)
            
            # If successful, replace the original file
            if os.path.exists(temp_file):
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
                os.rename(temp_file, self.state_file)
                
        except Exception as e:
            print(f"Error saving state file: {str(e)}")
            # Clean up temporary file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def save_state(self, strategy: str, state: MarketState) -> None:
        """Save the trading state for a specific strategy"""
        try:
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
            self._save_states()
        except Exception as e:
            print(f"Error saving state for strategy {strategy}: {str(e)}")
    
    def load_state(self, strategy: str) -> TradingState:
        """Load the trading state for a specific strategy"""
        return self.states.get(strategy, {})
    
    def get_all_states(self) -> Dict[str, TradingState]:
        """Get all saved trading states"""
        return self.states
    
    def clear_state(self, strategy: str = None) -> None:
        """Clear trading state for a specific strategy or all strategies"""
        try:
            if strategy:
                if strategy in self.states:
                    del self.states[strategy]
            else:
                self.states = {}
            
            # Save updated states
            self._save_states()
        except Exception as e:
            print(f"Error clearing state: {str(e)}")
    
    def restore_from_backup(self) -> bool:
        """Restore state from backup file"""
        if not os.path.exists(self.backup_file):
            print("No backup file found")
            return False
        
        try:
            # Create backup of current state file
            self._backup_state_file()
            
            # Restore from backup
            shutil.copy2(self.backup_file, self.state_file)
            
            # Reload states
            self._load_states()
            return True
        except Exception as e:
            print(f"Error restoring from backup: {str(e)}")
            return False 