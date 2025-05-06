from typing import Dict, List, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from config.config import AGENT_TEMPERATURE, AGENT_MODEL

class TradingStrategy:
    """Trading strategy configuration"""
    def __init__(self, name: str, description: str, risk_level: str, target_return: float):
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.target_return = target_return

# Define trading strategies
STRATEGIES = {
    'aggressive': TradingStrategy(
        name="Maximum Returns",
        description="""Aggressive strategy focused on maximizing returns through high-risk, high-reward trades.
        Key characteristics:
        - Takes larger positions in volatile assets
        - Uses leverage when available
        - Focuses on momentum and trend following
        - Quick entry and exit from positions
        - Embraces meme coins and high-volatility tokens
        - Uses social sentiment for trading signals
        - Maintains minimal USDT reserves
        - Targets 1000%+ returns on successful trades
        - Aims for 100x portfolio growth""",
        risk_level="high",
        target_return=1000.0
    ),
    'balanced': TradingStrategy(
        name="Balanced Growth",
        description="""Balanced strategy that combines aggressive and conservative approaches.
        Key characteristics:
        - Diversifies across multiple asset classes
        - Takes calculated risks on promising projects
        - Maintains moderate position sizes
        - Uses both technical and fundamental analysis
        - Keeps some USDT for opportunities
        - Targets 500%+ returns on successful trades
        - Aims for 50x portfolio growth""",
        risk_level="medium",
        target_return=500.0
    ),
    'conservative': TradingStrategy(
        name="Safe Growth",
        description="""Conservative strategy focused on steady growth with controlled risk.
        Key characteristics:
        - Focuses on established cryptocurrencies
        - Takes smaller, well-researched positions
        - Uses strict stop-losses
        - Emphasizes fundamental analysis
        - Maintains higher USDT reserves
        - Targets 200%+ returns on successful trades
        - Aims for 20x portfolio growth""",
        risk_level="low",
        target_return=200.0
    )
}

class MarketState(TypedDict):
    """State of the market analysis workflow"""
    current_prices: Dict[str, float]
    portfolio_value: float
    progress_to_target: float
    positions: Dict[str, Dict]
    available_balance: float
    market_analysis: str
    risk_assessment: str
    trading_plan: str
    executed_trades: List[Dict]
    strategy: str 