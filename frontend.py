import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict
from utils.test_wallet import TestWallet
from utils.binance_utils import BinanceWrapper
from agents.trading_agents import TradingAgents, MarketState
from agents.trading_strategies import STRATEGIES
from config.config import (
    MAJOR_COINS,
    MEME_COINS,
    DEFI_COINS,
    TRADING_COINS,
    INITIAL_BALANCE,
    TARGET_BALANCE
)
from utils.state_manager import StateManager

def create_price_chart(prices: dict, title: str):
    """Create a price chart using Plotly"""
    fig = go.Figure()
    for symbol, price in prices.items():
        fig.add_trace(go.Scatter(
            x=[datetime.now()],
            y=[price],
            name=symbol,
            mode='lines+markers'
        ))
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        height=400,
        showlegend=True
    )
    return fig

def create_performance_chart(wallets: Dict[str, TestWallet], current_prices: Dict[str, float]):
    """Create a performance chart comparing all traders"""
    fig = go.Figure()
    
    for strategy, wallet in wallets.items():
        trade_history = wallet.trade_history
        if not trade_history:
            continue
        
        df = pd.DataFrame([{
            'timestamp': trade.timestamp,
            'profit_loss': trade.profit_loss if trade.profit_loss is not None else 0
        } for trade in trade_history])
        
        df['cumulative_pnl'] = df['profit_loss'].cumsum()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cumulative_pnl'],
            name=f"{STRATEGIES[strategy].name}",
            mode='lines'
        ))
    
    fig.update_layout(
        title='Traders Performance Comparison',
        xaxis_title='Time',
        yaxis_title='Cumulative P&L (USDT)',
        height=400,
        showlegend=True
    )
    return fig

def format_currency(value: float) -> str:
    """Format currency values with appropriate precision"""
    return f"${value:.2f}"

def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.1f}%"

def main():
    st.set_page_config(page_title="Multi-Strategy CryptoTrader Dashboard", layout="wide")
    st.title("Multi-Strategy CryptoTrader Dashboard")
    
    # Initialize components
    if 'wallets' not in st.session_state:
        # Get current BTC price first
        binance = BinanceWrapper()
        btc_price = binance.get_current_price('BTCUSDT')
        
        # Create wallets with initial BTC purchase
        st.session_state.wallets = {}
        for strategy in STRATEGIES.keys():
            wallet = TestWallet(INITIAL_BALANCE, TARGET_BALANCE)
            if hasattr(wallet, 'initialize_with_btc'):
                wallet.initialize_with_btc(btc_price)
            st.session_state.wallets[strategy] = wallet
    
    if 'binance' not in st.session_state:
        st.session_state.binance = BinanceWrapper()
    
    if 'agents' not in st.session_state:
        st.session_state.agents = {
            strategy: TradingAgents(strategy)
            for strategy in STRATEGIES.keys()
        }
    
    if 'state_manager' not in st.session_state:
        st.session_state.state_manager = StateManager()
    
    # Sidebar controls
    st.sidebar.header("Controls")
    auto_trading = st.sidebar.checkbox("Enable Auto Trading", value=False)
    update_interval = st.sidebar.slider("Update Interval (seconds)", 5, 60, 10)
    
    # Strategy selection
    st.sidebar.header("Active Strategies")
    active_strategies = {
        strategy: st.sidebar.checkbox(f"{STRATEGIES[strategy].name}", value=True)
        for strategy in STRATEGIES.keys()
    }
    
    # Coin category selection
    st.sidebar.header("Coin Categories")
    show_major = st.sidebar.checkbox("Major Coins", value=True)
    show_meme = st.sidebar.checkbox("Meme Coins", value=True)
    show_defi = st.sidebar.checkbox("DeFi Coins", value=True)
    
    # Get current market data
    current_prices = {
        symbol: st.session_state.binance.get_current_price(symbol)
        for symbol in TRADING_COINS
    }
    
    # Market Overview
    st.subheader("Market Overview")
    
    # Filter prices based on selected categories
    filtered_prices = {}
    if show_major:
        filtered_prices.update({k: v for k, v in current_prices.items() if k in MAJOR_COINS})
    if show_meme:
        filtered_prices.update({k: v for k, v in current_prices.items() if k in MEME_COINS})
    if show_defi:
        filtered_prices.update({k: v for k, v in current_prices.items() if k in DEFI_COINS})
    
    price_chart = create_price_chart(filtered_prices, "Current Prices")
    st.plotly_chart(price_chart, use_container_width=True)
    
    # Performance Comparison
    performance_chart = create_performance_chart(st.session_state.wallets, current_prices)
    st.plotly_chart(performance_chart, use_container_width=True)
    
    # Individual Trader Portfolios
    st.subheader("Trader Portfolios")
    
    # Create columns for each active strategy
    cols = st.columns(len([s for s, active in active_strategies.items() if active]))
    col_idx = 0
    
    for strategy, active in active_strategies.items():
        if not active:
            continue
            
        wallet = st.session_state.wallets[strategy]
        portfolio_value = wallet.get_total_value(current_prices)
        progress = wallet.get_progress_to_target(current_prices)
        metrics = wallet.get_performance_summary()
        
        # Load saved state
        saved_state = st.session_state.state_manager.load_state(strategy)
        
        with cols[col_idx]:
            st.markdown(f"### {STRATEGIES[strategy].name}")
            st.markdown(f"*{STRATEGIES[strategy].description}*")
            
            # Portfolio metrics
            st.metric(
                "Portfolio Value",
                format_currency(portfolio_value),
                format_percentage(progress)
            )
            st.metric(
                "Total P&L",
                format_currency(metrics['total_profit_loss']),
                format_percentage((metrics['total_profit_loss'] / INITIAL_BALANCE) * 100)
            )
            st.metric(
                "Win Rate",
                format_percentage(metrics['win_rate']),
                f"{metrics['winning_trades']}/{metrics['total_trades']} trades"
            )
            
            # Current positions
            if wallet.positions:
                st.markdown("#### Current Holdings")
                positions_data = []
                for symbol, pos in wallet.positions.items():
                    current_price = current_prices.get(symbol, 0)
                    entry_price = pos['entry_price']
                    amount = pos['amount']
                    current_value = amount * current_price
                    entry_value = amount * entry_price
                    pnl = current_value - entry_value
                    pnl_percentage = (pnl / entry_value) * 100
                    
                    positions_data.append({
                        'Symbol': symbol,
                        'Amount': f"{amount:.4f}",
                        'Entry': format_currency(entry_price),
                        'Current': format_currency(current_price),
                        'Value': format_currency(current_value),
                        'P&L': format_currency(pnl),
                        'P&L %': format_percentage(pnl_percentage)
                    })
                
                positions_df = pd.DataFrame(positions_data)
                st.dataframe(
                    positions_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No open positions")
            
            # Latest trades
            if wallet.trade_history:
                st.markdown("#### Latest Trades")
                latest_trades = wallet.trade_history[-5:]  # Show last 5 trades
                for trade in reversed(latest_trades):
                    st.markdown(f"""
                    - **{trade.type.upper()}** {trade.amount:.4f} {trade.symbol}
                    - Price: {format_currency(trade.price)}
                    - Total: {format_currency(trade.total)}
                    - P&L: {format_currency(trade.profit_loss) if trade.profit_loss is not None else '-'}
                    """)
            
            # Create two columns for the trade execution section
            col1, col2 = st.columns(2)
            
            with col1:
                # Latest Trade Execution
                st.subheader("Latest Trade Execution")
                
                # Market Analysis
                if 'market_analysis' in saved_state:
                    with st.expander("Market Analysis"):
                        st.write(saved_state['market_analysis'])
                
                # Risk Assessment
                if 'risk_assessment' in saved_state:
                    with st.expander("Risk Assessment"):
                        st.write(saved_state['risk_assessment'])
                
                # Financial Advice
                if 'financial_advice' in saved_state:
                    with st.expander("Financial Advice"):
                        st.write(saved_state['financial_advice'])
            
            with col2:
                # Risk Analysis
                if 'risk_analysis' in saved_state:
                    with st.expander("Detailed Risk Analysis"):
                        st.write(saved_state['risk_analysis'])
                
                # Trading Plan
                if 'trading_plan' in saved_state:
                    with st.expander("Trading Plan"):
                        st.write(saved_state['trading_plan'])
                
                # Executed Trades
                if 'executed_trades' in saved_state and saved_state['executed_trades']:
                    with st.expander("Executed Trades"):
                        for trade in saved_state['executed_trades']:
                            st.write(f"**{trade['type']}** {trade['amount']} {trade['symbol']}")
                            st.write(f"Reason: {trade['reason']}")
                            st.write("---")
        
        col_idx += 1
    
    # Auto trading logic
    if auto_trading:
        if st.button("Stop Auto Trading"):
            auto_trading = False
            st.rerun()
        
        for strategy, active in active_strategies.items():
            if not active:
                continue
                
            wallet = st.session_state.wallets[strategy]
            agents = st.session_state.agents[strategy]
            
            # Load previous state
            previous_state = st.session_state.state_manager.load_state(strategy)
            
            # Create market state
            state = MarketState(
                current_prices=current_prices,
                portfolio_value=wallet.get_total_value(current_prices),
                progress_to_target=wallet.get_progress_to_target(current_prices),
                positions=wallet.positions,
                available_balance=wallet.balance,
                market_analysis=previous_state.get('market_analysis', ''),
                risk_assessment=previous_state.get('risk_assessment', ''),
                financial_advice=previous_state.get('financial_advice', ''),
                risk_analysis=previous_state.get('risk_analysis', ''),
                trading_plan=previous_state.get('trading_plan', ''),
                executed_trades=previous_state.get('executed_trades', []),
                strategy=strategy
            )
            
            # Run trading workflow
            state = agents.run_trading_workflow(state)
            
            # Save updated state
            st.session_state.state_manager.save_state(strategy, state)
            
            # Execute trades
            if state['executed_trades']:
                for trade in state['executed_trades']:
                    if trade['type'] == 'BUY':
                        current_price = current_prices.get(trade['symbol'])
                        if current_price:
                            wallet.buy(trade['symbol'], trade['amount'], current_price)
                    elif trade['type'] == 'SELL':
                        current_price = current_prices.get(trade['symbol'])
                        if current_price:
                            wallet.sell(trade['symbol'], trade['amount'], current_price)
        
        # Auto-refresh
        time.sleep(update_interval)
        st.rerun()
    else:
        if st.button("Start Auto Trading"):
            auto_trading = True
            st.rerun()

if __name__ == "__main__":
    main() 