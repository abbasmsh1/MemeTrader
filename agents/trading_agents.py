import json
from typing import Dict, List, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_together import Together
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.binance_utils import BinanceWrapper
from utils.tools import HistoricalKlinesTool, CurrentPriceTool, Stats24hTool
from config.config import AGENT_TEMPERATURE, AGENT_MODEL
from .trading_strategies import STRATEGIES, TradingStrategy

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

class TradingAgents:
    def __init__(self, strategy: str = 'conservative'):
        self.binance = BinanceWrapper()
        self.tools = {
            'historical_klines': HistoricalKlinesTool(binance=self.binance),
            'current_price': CurrentPriceTool(binance=self.binance),
            'stats_24h': Stats24hTool(binance=self.binance)
        }
        
        # Initialize Together AI LLM
        self.llm = Together(
            model=AGENT_MODEL,
            temperature=AGENT_TEMPERATURE,
            max_tokens=1000
        )
        
        # Set strategy
        self.strategy = STRATEGIES.get(strategy, STRATEGIES['conservative'])
        
        # Create agent prompts
        self.market_analyst_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a professional cryptocurrency market analyst specializing in {self.strategy.name}.
            Analyze the current market conditions and provide insights about potential trading opportunities.
            Focus on identifying trends, support/resistance levels, and market sentiment.
            {self.strategy.description}"""),
            ("human", """Current market prices:
            {current_prices}
            
            Portfolio value: ${portfolio_value}
            Progress to target: {progress_to_target}%
            Current positions: {positions}
            Available balance: ${available_balance}
            
            Please analyze the market and provide your insights.""")
        ])
        
        self.risk_manager_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a risk management expert for cryptocurrency trading, specializing in {self.strategy.name}.
            Assess the risks associated with potential trades and provide risk management recommendations.
            Consider market volatility, portfolio exposure, and risk-reward ratios.
            {self.strategy.description}"""),
            ("human", """Market Analysis:
            {market_analysis}
            
            Current positions: {positions}
            Available balance: ${available_balance}
            
            Please assess the risks and provide recommendations.""")
        ])
        
        self.trader_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a professional cryptocurrency trader specializing in {self.strategy.name}.
            Create a detailed trading plan based on market analysis and risk assessment.
            Specify exact amounts to buy or sell for each cryptocurrency.
            {self.strategy.description}"""),
            ("human", """Market Analysis:
            {market_analysis}
            
            Risk Assessment:
            {risk_assessment}
            
            Current positions: {positions}
            Available balance: ${available_balance}
            
            Please create a detailed trading plan with specific actions.""")
        ])
        
        # Trade Executor Prompt
        example_json = r'''[
  {
    "type": "BUY",
    "symbol": "BTCUSDT",
    "amount": 0.001,
    "reason": "Buying BTC based on positive market analysis"
  }
]'''

        self.executor_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a precise trade executor for cryptocurrency trading, specializing in {self.strategy.name}.
            Your role is to interpret the trading plan and execute trades exactly as specified.
            You must ensure all trades meet the minimum purchase amount of $5.
            
            You MUST respond with a valid JSON array of trade actions. Each action must have these exact fields:
            - type: "BUY" or "SELL"
            - symbol: The trading pair (e.g., "BTCUSDT")
            - amount: The exact amount to trade
            - reason: A brief explanation of why this trade is being executed
            
            Example response format (copy this exactly):
            {example_json}
            
            {self.strategy.description}"""),
            ("human", """Trading Plan:
            {trading_plan}
            
            Current prices:
            {current_prices}
            
            Current positions: {positions}
            Available balance: ${available_balance}
            
            Please execute the trades exactly as specified in the plan. Remember to respond with a valid JSON array.""")
        ])
        
        # Create agent chains
        self.market_analyst_chain = self.market_analyst_prompt | self.llm | StrOutputParser()
        self.risk_manager_chain = self.risk_manager_prompt | self.llm | StrOutputParser()
        self.trader_chain = self.trader_prompt | self.llm | StrOutputParser()
        self.executor_chain = self.executor_prompt | self.llm | StrOutputParser()
    
    def analyze_market(self, state: MarketState) -> MarketState:
        """Analyze market conditions"""
        state['market_analysis'] = self.market_analyst_chain.invoke({
            'current_prices': state['current_prices'],
            'portfolio_value': state['portfolio_value'],
            'progress_to_target': state['progress_to_target'],
            'positions': state['positions'],
            'available_balance': state['available_balance']
        })
        return state
    
    def assess_risk(self, state: MarketState) -> MarketState:
        """Assess trading risks"""
        state['risk_assessment'] = self.risk_manager_chain.invoke({
            'market_analysis': state['market_analysis'],
            'positions': state['positions'],
            'available_balance': state['available_balance']
        })
        return state
    
    def create_trading_plan(self, state: MarketState) -> MarketState:
        """Create trading plan"""
        state['trading_plan'] = self.trader_chain.invoke({
            'market_analysis': state['market_analysis'],
            'risk_assessment': state['risk_assessment'],
            'positions': state['positions'],
            'available_balance': state['available_balance']
        })
        return state
    
    def execute_trades(self, state: MarketState) -> MarketState:
        """Execute trades based on the trading plan"""
        # Initialize executed_trades if not present
        if 'executed_trades' not in state:
            state['executed_trades'] = []
        
        try:
            # Get trade execution instructions
            execution_instructions = self.executor_chain.invoke({
                'trading_plan': state['trading_plan'],
                'current_prices': state['current_prices'],
                'positions': state['positions'],
                'available_balance': state['available_balance']
            })
            
            # Clean the response to ensure it's valid JSON
            execution_instructions = execution_instructions.strip()
            if not execution_instructions.startswith('['):
                execution_instructions = '[' + execution_instructions
            if not execution_instructions.endswith(']'):
                execution_instructions = execution_instructions + ']'
            
            # Parse and validate trade instructions
            trades = json.loads(execution_instructions)
            
            # Validate each trade
            valid_trades = []
            for trade in trades:
                if all(key in trade for key in ['type', 'symbol', 'amount', 'reason']):
                    if trade['type'] in ['BUY', 'SELL']:
                        if trade['symbol'] in state['current_prices']:
                            if isinstance(trade['amount'], (int, float)) and trade['amount'] > 0:
                                valid_trades.append(trade)
            
            state['executed_trades'].extend(valid_trades)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing trade execution instructions: {str(e)}")
            print(f"Raw instructions: {execution_instructions}")
        except Exception as e:
            print(f"Error in trade execution: {str(e)}")
        
        return state 