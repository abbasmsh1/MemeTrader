from typing import Dict, List, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from config.config import AGENT_TEMPERATURE, AGENT_MODEL

class TradingStrategy:
    """Trading strategy configuration"""
    def __init__(self, name: str, description: str, risk_level: str, target_return: float, 
                 max_position_size: float, min_position_size: float, max_leverage: float,
                 stop_loss_percentage: float, take_profit_percentage: float,
                 portfolio_allocation: Dict[str, float], max_drawdown: float,
                 rebalance_threshold: float, sector_focus: List[str]):
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.target_return = target_return
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.max_leverage = max_leverage
        self.stop_loss_percentage = stop_loss_percentage
        self.take_profit_percentage = take_profit_percentage
        self.portfolio_allocation = portfolio_allocation
        self.max_drawdown = max_drawdown
        self.rebalance_threshold = rebalance_threshold
        self.sector_focus = sector_focus

# Define trading strategies
STRATEGIES = {
    'quantitative': TradingStrategy(
        name="Quantitative Alpha",
        description="""Advanced quantitative strategy using algorithmic trading and statistical arbitrage.
        Key characteristics:
        - Uses machine learning for market prediction
        - Implements high-frequency trading strategies
        - Focuses on market inefficiencies
        - Employs statistical arbitrage
        - Uses complex derivatives and options
        - Maintains strict risk controls
        - Targets 300%+ annual returns
        - Aims for consistent alpha generation""",
        risk_level="high",
        target_return=300.0,
        max_position_size=0.25,
        min_position_size=0.05,
        max_leverage=3.0,
        stop_loss_percentage=8.0,
        take_profit_percentage=15.0,
        portfolio_allocation={
            'crypto': 0.4,
            'defi': 0.3,
            'derivatives': 0.2,
            'stablecoins': 0.1
        },
        max_drawdown=0.15,
        rebalance_threshold=0.1,
        sector_focus=['defi', 'derivatives', 'lending']
    ),
    'fundamental': TradingStrategy(
        name="Fundamental Value",
        description="""Long-term value investing strategy focusing on fundamental analysis.
        Key characteristics:
        - Deep research into project fundamentals
        - Long-term position holding
        - Focus on network effects and adoption
        - Emphasis on team and technology
        - Conservative position sizing
        - Targets 100%+ annual returns
        - Aims for sustainable growth""",
        risk_level="low",
        target_return=100.0,
        max_position_size=0.15,
        min_position_size=0.02,
        max_leverage=1.0,
        stop_loss_percentage=5.0,
        take_profit_percentage=30.0,
        portfolio_allocation={
            'crypto': 0.6,
            'defi': 0.2,
            'stablecoins': 0.2
        },
        max_drawdown=0.10,
        rebalance_threshold=0.15,
        sector_focus=['infrastructure', 'l1', 'l2']
    ),
    'momentum': TradingStrategy(
        name="Momentum Trading",
        description="""Dynamic strategy focusing on market momentum and trend following.
        Key characteristics:
        - Technical analysis based
        - Quick entry and exit
        - Trend following approach
        - Volume analysis
        - Multiple timeframe analysis
        - Targets 200%+ annual returns
        - Aims for consistent momentum capture""",
        risk_level="medium",
        target_return=200.0,
        max_position_size=0.2,
        min_position_size=0.03,
        max_leverage=2.0,
        stop_loss_percentage=7.0,
        take_profit_percentage=20.0,
        portfolio_allocation={
            'crypto': 0.5,
            'defi': 0.3,
            'stablecoins': 0.2
        },
        max_drawdown=0.12,
        rebalance_threshold=0.12,
        sector_focus=['meme', 'gaming', 'social']
    ),
    'arbitrage': TradingStrategy(
        name="Cross-Exchange Arbitrage",
        description="""Strategy focused on exploiting price differences across exchanges.
        Key characteristics:
        - Multi-exchange trading
        - High-frequency execution
        - Low latency infrastructure
        - Focus on liquidity provision
        - Minimal directional exposure
        - Targets 150%+ annual returns
        - Aims for consistent arbitrage opportunities""",
        risk_level="low",
        target_return=150.0,
        max_position_size=0.3,
        min_position_size=0.05,
        max_leverage=1.5,
        stop_loss_percentage=3.0,
        take_profit_percentage=1.0,
        portfolio_allocation={
            'crypto': 0.7,
            'stablecoins': 0.3
        },
        max_drawdown=0.08,
        rebalance_threshold=0.05,
        sector_focus=['major_crypto', 'stablecoins']
    ),
    'venture': TradingStrategy(
        name="Venture Capital",
        description="""Early-stage investment strategy focusing on promising projects.
        Key characteristics:
        - Early token investments
        - Project incubation
        - Strategic partnerships
        - Long-term holding
        - High conviction bets
        - Targets 500%+ annual returns
        - Aims for asymmetric returns""",
        risk_level="very_high",
        target_return=500.0,
        max_position_size=0.4,
        min_position_size=0.1,
        max_leverage=1.0,
        stop_loss_percentage=20.0,
        take_profit_percentage=200.0,
        portfolio_allocation={
            'crypto': 0.3,
            'defi': 0.4,
            'gaming': 0.2,
            'stablecoins': 0.1
        },
        max_drawdown=0.25,
        rebalance_threshold=0.2,
        sector_focus=['gaming', 'defi', 'infrastructure']
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
    department: str
    trader: str
    performance_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    allocation_metrics: Dict[str, float] 