import os
import sys
from typing import Dict, TypedDict, Annotated, List
from langgraph.graph import Graph, StateGraph
from agents.trading_agents import TradingAgents, MarketState
from utils.binance_utils import BinanceWrapper
from utils.wallet import SimulatedWallet
from utils.test_wallet import TestWallet
from config.config import (
    MEME_COINS,
    TRADING_COINS,
    TRADING_INTERVAL,
    INITIAL_BALANCE,
    TARGET_BALANCE,
    MAX_RISK_PER_TRADE,
    STOP_LOSS_PERCENTAGE,
    TAKE_PROFIT_PERCENTAGE
)
import time
from datetime import datetime, timedelta
import re
from utils.state_manager import StateManager

def create_trading_workflow(trading_agents: TradingAgents, state_manager: StateManager) -> Graph:
    """Create the trading workflow using LangGraph"""
    
    # Create workflow
    workflow = StateGraph(MarketState)
    
    # Add nodes
    workflow.add_node("market_analyst", trading_agents.analyze_market)
    workflow.add_node("risk_manager", trading_agents.assess_risk)
    workflow.add_node("financial_advisor", trading_agents.get_financial_advice)
    workflow.add_node("risk_analyzer", trading_agents.analyze_risk)
    workflow.add_node("trader", trading_agents.create_trading_plan)
    workflow.add_node("executor", trading_agents.execute_trades)
    
    # Add edges
    workflow.add_edge("market_analyst", "risk_manager")
    workflow.add_edge("risk_manager", "financial_advisor")
    workflow.add_edge("financial_advisor", "risk_analyzer")
    workflow.add_edge("risk_analyzer", "trader")
    workflow.add_edge("trader", "executor")
    
    # Set entry point
    workflow.set_entry_point("market_analyst")
    
    # Compile workflow
    app = workflow.compile()
    
    return app

def parse_trading_plan(plan: str, current_prices: Dict[str, float]) -> List[Dict]:
    """Parse the trading plan into executable actions"""
    actions = []
    
    # Look for buy/sell recommendations
    buy_pattern = r"buy\s+(\d+(?:\.\d+)?)\s+(\w+)(?:USDT)?"
    sell_pattern = r"sell\s+(\d+(?:\.\d+)?)\s+(\w+)(?:USDT)?"
    
    # Find buy recommendations
    for match in re.finditer(buy_pattern, plan.lower()):
        amount, symbol = match.groups()
        symbol = f"{symbol.upper()}USDT"
        if symbol in current_prices:
            actions.append({
                'type': 'BUY',
                'symbol': symbol,
                'amount': float(amount),
                'price': current_prices[symbol]
            })
    
    # Find sell recommendations
    for match in re.finditer(sell_pattern, plan.lower()):
        amount, symbol = match.groups()
        symbol = f"{symbol.upper()}USDT"
        if symbol in current_prices:
            actions.append({
                'type': 'SELL',
                'symbol': symbol,
                'amount': float(amount),
                'price': current_prices[symbol]
            })
    
    return actions

def execute_trades(actions: List[Dict], wallet: TestWallet) -> None:
    """Execute the trading actions"""
    for action in actions:
        try:
            if action['type'] == 'BUY':
                success = wallet.buy(
                    action['symbol'],
                    action['amount'],
                    action['price']
                )
                if success:
                    print(f"✅ Executed buy: {action['amount']} {action['symbol']} at ${action['price']:.4f}")
                    print(f"Reason: {action.get('reason', 'No reason provided')}")
                else:
                    print(f"❌ Failed to execute buy: {action['amount']} {action['symbol']}")
            
            elif action['type'] == 'SELL':
                success = wallet.sell(
                    action['symbol'],
                    action['amount'],
                    action['price']
                )
                if success:
                    print(f"✅ Executed sell: {action['amount']} {action['symbol']} at ${action['price']:.4f}")
                    print(f"Reason: {action.get('reason', 'No reason provided')}")
                else:
                    print(f"❌ Failed to execute sell: {action['amount']} {action['symbol']}")
        
        except Exception as e:
            print(f"Error executing trade: {str(e)}")

def main():
    # Initialize components
    binance = BinanceWrapper()
    wallet = TestWallet(INITIAL_BALANCE, TARGET_BALANCE)
    agents = TradingAgents()
    state_manager = StateManager()
    
    # Initialize wallet with BTC purchase
    btc_price = binance.get_current_price('BTCUSDT')
    wallet.initialize_with_btc(btc_price)
    
    # Create trading workflow
    workflow = create_trading_workflow(agents, state_manager)
    
    print(f"Starting trading with initial balance: ${INITIAL_BALANCE}")
    print(f"Target balance: ${TARGET_BALANCE}")
    print(f"Initial BTC purchase: {wallet.positions.get('BTCUSDT', {}).get('amount', 0):.8f} BTC")
    
    while True:
        try:
            # Get current market data
            current_prices = {
                symbol: binance.get_current_price(symbol)
                for symbol in TRADING_COINS
            }
            
            # Calculate current portfolio value
            portfolio_value = wallet.get_total_value(current_prices)
            progress = wallet.get_progress_to_target(current_prices)
            
            # Load previous state if exists
            previous_state = state_manager.load_state(agents.strategy)
            
            # Initialize workflow state
            initial_state = {
                'current_prices': current_prices,
                'portfolio_value': portfolio_value,
                'progress_to_target': progress,
                'positions': wallet.positions,
                'available_balance': wallet.balance,
                'market_analysis': previous_state.get('market_analysis', ''),
                'risk_assessment': previous_state.get('risk_assessment', ''),
                'financial_advice': previous_state.get('financial_advice', ''),
                'risk_analysis': previous_state.get('risk_analysis', ''),
                'trading_plan': previous_state.get('trading_plan', ''),
                'executed_trades': previous_state.get('executed_trades', [])
            }
            
            # Run trading workflow
            result = workflow.invoke(initial_state)
            
            # Save the updated state
            state_manager.save_state(agents.strategy, result)
            
            # Print results
            print("\nTrading Cycle Results:")
            print(f"Portfolio Value: ${portfolio_value:.2f}")
            print(f"Progress to Target: {progress:.1f}%")
            print("\nMarket Analysis:")
            print(result['market_analysis'])
            print("\nRisk Assessment:")
            print(result['risk_assessment'])
            print("\nFinancial Advice:")
            print(result['financial_advice'])
            print("\nRisk Analysis:")
            print(result['risk_analysis'])
            print("\nTrading Plan:")
            print(result['trading_plan'])
            
            # Execute trades
            if result['executed_trades']:
                print("\nExecuting trades:")
                execute_trades(result['executed_trades'], wallet)
            
            # Check if target reached
            if portfolio_value >= TARGET_BALANCE:
                print("\nTarget balance reached! Stopping trading.")
                break
            
            # Wait for next trading interval
            time.sleep(TRADING_INTERVAL)
            
        except Exception as e:
            print(f"Error in trading cycle: {str(e)}")
            time.sleep(TRADING_INTERVAL)

if __name__ == "__main__":
    main() 