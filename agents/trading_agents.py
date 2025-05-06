import json
import time
import re
from typing import Dict, List, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_together import Together
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.binance_utils import BinanceWrapper
from utils.tools import HistoricalKlinesTool, CurrentPriceTool, Stats24hTool
from config.config import AGENT_TEMPERATURE, AGENT_MODEL
from .trading_strategies import STRATEGIES, TradingStrategy

def parse_fraction(fraction_str: str) -> float:
    """Parse a fraction string into a float value"""
    try:
        return eval(fraction_str)
    except:
        return float(fraction_str)

def fix_json_fractions(json_str: str) -> str:
    """Fix fractions in JSON string by converting them to decimal values"""
    def replace_fraction(match):
        try:
            return str(parse_fraction(match.group(0)))
        except:
            return match.group(0)
    
    return re.sub(r'\d+/\d+', replace_fraction, json_str)

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
    financial_advice: str
    risk_analysis: str

class TradingPersonality:
    """Base class for trading personalities"""
    def __init__(self, name: str, description: str, risk_level: str, style: str):
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.style = style

# Define trading personalities
TRADING_PERSONALITIES = {
    'elon': TradingPersonality(
        name="Elon Musk",
        description="""High-risk, high-reward trader who focuses on disruptive technologies and meme coins.
        Known for making bold market moves and influencing prices through social media.
        Tends to favor innovative projects and often makes unexpected trades.""",
        risk_level="aggressive",
        style="disruptive"
    ),
    'cathie': TradingPersonality(
        name="Cathie Wood",
        description="""Innovation-focused investor who looks for disruptive technologies.
        Takes long-term positions in high-growth sectors.
        Believes in the transformative power of technology.""",
        risk_level="moderate",
        style="innovative"
    ),
    'michael': TradingPersonality(
        name="Michael Saylor",
        description="""Bitcoin maximalist who focuses on long-term value storage.
        Believes in accumulating and holding Bitcoin as a primary strategy.
        Takes calculated risks based on fundamental analysis.""",
        risk_level="conservative",
        style="hodl"
    ),
    'cz': TradingPersonality(
        name="CZ (Changpeng Zhao)",
        description="""Exchange-focused trader who understands market mechanics deeply.
        Balances risk across multiple assets and strategies.
        Focuses on liquidity and market efficiency.""",
        risk_level="balanced",
        style="exchange"
    ),
    'vitalik': TradingPersonality(
        name="Vitalik Buterin",
        description="""Technical analyst who focuses on fundamental blockchain technology.
        Prefers projects with strong technical foundations.
        Takes calculated risks based on technical merit.""",
        risk_level="moderate",
        style="technical"
    )
}

# Define trading strategies
STRATEGIES = {
    'aggressive': TradingStrategy(
        name="Maximum Returns",
        description="""High-risk, high-reward strategy focusing on maximum returns.
        Key characteristics:
        - Aggressive position sizing
        - High leverage usage
        - Quick entry and exit
        - Focus on momentum and trends
        - Targets 1000%+ annual returns
        - Aims for asymmetric returns""",
        risk_level="high",
        target_return=1000.0,
        max_position_size=0.4,
        min_position_size=0.1,
        max_leverage=5.0,
        stop_loss_percentage=15.0,
        take_profit_percentage=100.0,
        portfolio_allocation={
            'crypto': 0.5,
            'defi': 0.3,
            'meme': 0.2
        },
        max_drawdown=0.25,
        rebalance_threshold=0.15,
        sector_focus=['meme', 'defi', 'gaming']
    ),
    'balanced': TradingStrategy(
        name="Balanced Growth",
        description="""Balanced strategy combining aggressive and conservative approaches.
        Key characteristics:
        - Moderate position sizing
        - Controlled leverage usage
        - Mix of short and long-term positions
        - Focus on both momentum and value
        - Targets 500%+ annual returns
        - Aims for consistent growth""",
        risk_level="medium",
        target_return=500.0,
        max_position_size=0.3,
        min_position_size=0.05,
        max_leverage=3.0,
        stop_loss_percentage=10.0,
        take_profit_percentage=50.0,
        portfolio_allocation={
            'crypto': 0.4,
            'defi': 0.3,
            'stablecoins': 0.3
        },
        max_drawdown=0.15,
        rebalance_threshold=0.1,
        sector_focus=['defi', 'infrastructure', 'l1']
    ),
    'conservative': TradingStrategy(
        name="Safe Growth",
        description="""Conservative strategy focusing on steady growth with controlled risk.
        Key characteristics:
        - Small position sizes
        - Minimal leverage usage
        - Long-term holding
        - Focus on fundamental value
        - Targets 200%+ annual returns
        - Aims for sustainable growth""",
        risk_level="low",
        target_return=200.0,
        max_position_size=0.2,
        min_position_size=0.02,
        max_leverage=1.5,
        stop_loss_percentage=5.0,
        take_profit_percentage=20.0,
        portfolio_allocation={
            'crypto': 0.3,
            'defi': 0.2,
            'stablecoins': 0.5
        },
        max_drawdown=0.10,
        rebalance_threshold=0.05,
        sector_focus=['infrastructure', 'l1', 'l2']
    )
}

class TradingAgents:
    def __init__(self, personality: str = 'elon', strategy: str = 'aggressive'):
        self.binance = BinanceWrapper()
        self.tools = {
            'historical_klines': HistoricalKlinesTool(binance=self.binance),
            'current_price': CurrentPriceTool(binance=self.binance),
            'stats_24h': Stats24hTool(binance=self.binance)
        }
        
        # Initialize Together AI LLM with rate limiting
        self.llm = Together(
            model=AGENT_MODEL,
            temperature=AGENT_TEMPERATURE,
            max_tokens=1000
        )
        
        # Rate limiting settings
        self.last_request_time = 0
        self.min_request_interval = 1.1  # Slightly more than 1 second to stay under 1 QPS
        
        # Set personality and strategy
        self.personality = TRADING_PERSONALITIES.get(personality, TRADING_PERSONALITIES['elon'])
        self.strategy = STRATEGIES.get(strategy, STRATEGIES['aggressive'])
        
        # Initialize position fields
        self.position_fields = {
            'amount': 0.0,
            'average_price': 0.0,
            'total_value': 0.0,
            'entry_price': 0.0
        }
        
        # Create agent prompts with personality
        self.market_analyst_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are {self.personality.name}, a professional cryptocurrency market analyst.
            Your trading style is {self.personality.style} and you take {self.personality.risk_level} risks.
            {self.personality.description}
            
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
        
        self.financial_advisor_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a professional financial advisor specializing in cryptocurrency portfolios.
            Your role is to provide high-level financial advice and portfolio optimization recommendations.
            Consider:
            - Portfolio diversification
            - Risk-adjusted returns
            - Market conditions
            - Long-term financial goals
            - Tax implications
            - Liquidity needs
            
            {self.strategy.description}"""),
            ("human", """Portfolio Overview:
            Current value: ${portfolio_value}
            Available balance: ${available_balance}
            Current positions: {positions}
            
            Market Analysis:
            {market_analysis}
            
            Risk Assessment:
            {risk_assessment}
            
            Please provide financial advice and portfolio optimization recommendations.""")
        ])
        
        self.risk_analyzer_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a detailed risk analyzer for cryptocurrency portfolios.
            Your role is to perform comprehensive risk analysis and portfolio risk assessment.
            Analyze:
            - Portfolio concentration risk
            - Market correlation risk
            - Volatility risk
            - Liquidity risk
            - Counterparty risk
            - Regulatory risk
            - Technical risk
            
            {self.strategy.description}"""),
            ("human", """Portfolio Overview:
            Current value: ${portfolio_value}
            Available balance: ${available_balance}
            Current positions: {positions}
            
            Market Analysis:
            {market_analysis}
            
            Risk Assessment:
            {risk_assessment}
            
            Financial Advice:
            {financial_advice}
            
            Please perform a detailed risk analysis of the portfolio.""")
        ])
        
        self.trader_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a professional cryptocurrency trader specializing in {self.strategy.name}.
            Create a detailed trading plan based on comprehensive market analysis, risk assessments, and financial advice.
            Consider all the following information in your trading decisions:
            
            1. Market Analysis:
            - Current market conditions and trends
            - Support/resistance levels
            - Market sentiment
            - Trading opportunities
            
            2. Risk Assessment:
            - Market volatility
            - Portfolio exposure
            - Risk-reward ratios
            - Risk management recommendations
            
            3. Financial Advice:
            - Portfolio diversification needs
            - Risk-adjusted return targets
            - Long-term financial goals
            - Tax implications
            - Liquidity requirements
            
            4. Risk Analysis:
            - Portfolio concentration risks
            - Market correlation risks
            - Volatility risks
            - Liquidity risks
            - Counterparty risks
            - Regulatory risks
            - Technical risks
            
            Your trading plan should:
            1. Align with the {self.strategy.name} strategy
            2. Consider all risk factors and financial advice
            3. Specify exact amounts to buy or sell for each cryptocurrency
            4. Include clear reasoning for each trade
            5. Ensure trades meet minimum purchase requirements
            6. Balance risk and reward appropriately
            
            {self.strategy.description}"""),
            ("human", """Market Analysis:
            {market_analysis}
            
            Risk Assessment:
            {risk_assessment}
            
            Financial Advice:
            {financial_advice}
            
            Risk Analysis:
            {risk_analysis}
            
            Current positions: {positions}
            Available balance: ${available_balance}
            
            Please create a detailed trading plan that considers all the above information.""")
        ])
        
        # Create the executor prompt
        self.executor_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a trade executor. Your role is to execute trades based on the trading plan and current market conditions.
            You must follow these rules:
            1. Only execute trades that are explicitly mentioned in the trading plan
            2. Never exceed the available balance
            3. Consider current positions when executing trades
            4. Always provide a clear reason for each trade
            5. Return ONLY a single JSON array containing trade objects
            6. DO NOT include any information or status messages
            7. DO NOT include multiple JSON arrays
            8. DO NOT include any text before or after the JSON array
            9. Only use valid trading pairs that are available in the current prices
            10. IMPORTANT: USDT is the quote currency - you CANNOT trade USDT directly
            11. To convert to USDT, sell the cryptocurrency you want to convert
            12. To convert from USDT, buy the cryptocurrency you want to purchase
            13. Valid trading pairs are:
                Major cryptocurrencies: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, ADAUSDT, XRPUSDT, DOGEUSDT
                Meme coins: PEPEUSDT, FLOKIUSDT, BONKUSDT, BOMEUSDT, WIFUSDT
                DeFi tokens: UNIUSDT, CAKEUSDT, SUSHIUSDT, COMPUSDT, AAVEUSDT, MKRUSDT, YFIUSDT, CRVUSDT
                Layer 1s: AVAXUSDT, MATICUSDT, DOTUSDT, LINKUSDT
                Other popular tokens: SHIBUSDT, LTCUSDT, ATOMUSDT, NEARUSDT, ALGOUSDT

            Available Balance: {available_balance}
            Current Prices: {current_prices}
            Current Positions: {positions}
            Trading Plan: {trading_plan}

            Return your trades in this exact format:
            [
                {{
                    "type": "buy" or "sell",
                    "symbol": "BTCUSDT" or "ETHUSDT" or "BNBUSDT" or "SOLUSDT" or "ADAUSDT" or "XRPUSDT" or "DOGEUSDT" or "PEPEUSDT" or "FLOKIUSDT" or "BONKUSDT" or "BOMEUSDT" or "WIFUSDT" or "UNIUSDT" or "CAKEUSDT" or "SUSHIUSDT" or "COMPUSDT" or "AAVEUSDT" or "MKRUSDT" or "YFIUSDT" or "CRVUSDT" or "AVAXUSDT" or "MATICUSDT" or "DOTUSDT" or "LINKUSDT" or "SHIBUSDT" or "LTCUSDT" or "ATOMUSDT" or "NEARUSDT" or "ALGOUSDT",
                    "amount": number,
                    "reason": "string explaining the trade"
                }}
            ]

            Example response:
            [
                {{
                    "type": "buy",
                    "symbol": "BTCUSDT",
                    "amount": 0.001,
                    "reason": "Buying BTC based on positive market analysis"
                }}
            ]

            Remember: 
            1. Return ONLY the JSON array with trade objects. No other text or information.
            2. Only use valid trading pairs from the list above.
            3. DO NOT try to trade USDT directly - it is the quote currency.
            4. To convert to USDT, sell the cryptocurrency.
            5. To convert from USDT, buy the cryptocurrency."""),
            ("human", "Execute trades based on the trading plan and current market conditions.")
        ])
        
        # Create agent chains
        self.market_analyst_chain = self.market_analyst_prompt | self.llm | StrOutputParser()
        self.risk_manager_chain = self.risk_manager_prompt | self.llm | StrOutputParser()
        self.financial_advisor_chain = self.financial_advisor_prompt | self.llm | StrOutputParser()
        self.risk_analyzer_chain = self.risk_analyzer_prompt | self.llm | StrOutputParser()
        self.trader_chain = self.trader_prompt | self.llm | StrOutputParser()
        self.executor_chain = self.executor_prompt | self.llm | StrOutputParser()

    def _rate_limited_invoke(self, chain, input_data, max_retries=3):
        """Invoke a chain with rate limiting and retry logic"""
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Add delay between retries
                if retry_count > 0:
                    delay = 2 ** retry_count  # Exponential backoff
                    print(f"Retrying in {delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(delay)
                
                result = chain.invoke(input_data)
                return result
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Check if it's a rate limit or server error
                if "rate limit" in str(e).lower() or "429" in str(e):
                    print(f"Rate limit hit. Waiting before retry...")
                elif "server" in str(e).lower() or "500" in str(e):
                    print(f"Server error. Retrying...")
                else:
                    print(f"Error during API call: {str(e)}")
                
                if retry_count == max_retries:
                    print(f"Max retries ({max_retries}) reached. Last error: {str(last_error)}")
                    # Return a default response instead of raising
                    if "financial_advice" in str(chain):
                        return "Unable to get financial advice at this time. Please proceed with caution."
                    elif "risk_analysis" in str(chain):
                        return "Unable to perform risk analysis at this time. Please proceed with caution."
                    elif "trading_plan" in str(chain):
                        return "Unable to create trading plan at this time. Please try again later."
                    else:
                        return "Service temporarily unavailable. Please try again later."
    
    def analyze_market(self, state: MarketState) -> MarketState:
        """Analyze market conditions"""
        state['market_analysis'] = self._rate_limited_invoke(
            self.market_analyst_chain,
            {
                'current_prices': state['current_prices'],
                'portfolio_value': state['portfolio_value'],
                'progress_to_target': state['progress_to_target'],
                'positions': state['positions'],
                'available_balance': state['available_balance']
            }
        )
        return state
    
    def assess_risk(self, state: MarketState) -> MarketState:
        """Assess trading risks"""
        state['risk_assessment'] = self._rate_limited_invoke(
            self.risk_manager_chain,
            {
                'market_analysis': state['market_analysis'],
                'positions': state['positions'],
                'available_balance': state['available_balance']
            }
        )
        return state
    
    def get_financial_advice(self, state: MarketState) -> MarketState:
        """Get financial advice and portfolio recommendations"""
        state['financial_advice'] = self._rate_limited_invoke(
            self.financial_advisor_chain,
            {
                'portfolio_value': state['portfolio_value'],
                'available_balance': state['available_balance'],
                'positions': state['positions'],
                'market_analysis': state['market_analysis'],
                'risk_assessment': state['risk_assessment']
            }
        )
        return state
    
    def analyze_risk(self, state: MarketState) -> MarketState:
        """Perform detailed risk analysis"""
        state['risk_analysis'] = self._rate_limited_invoke(
            self.risk_analyzer_chain,
            {
                'portfolio_value': state['portfolio_value'],
                'available_balance': state['available_balance'],
                'positions': state['positions'],
                'market_analysis': state['market_analysis'],
                'risk_assessment': state['risk_assessment'],
                'financial_advice': state['financial_advice']
            }
        )
        return state
    
    def create_trading_plan(self, state: MarketState) -> MarketState:
        """Create trading plan"""
        state['trading_plan'] = self._rate_limited_invoke(
            self.trader_chain,
            {
                'market_analysis': state['market_analysis'],
                'risk_assessment': state['risk_assessment'],
                'financial_advice': state['financial_advice'],
                'risk_analysis': state['risk_analysis'],
                'positions': state['positions'],
                'available_balance': state['available_balance']
            }
        )
        return state
    
    def _ensure_position_fields(self, position: dict, current_price: float) -> dict:
        """Ensure all required fields exist in a position"""
        for field, default_value in self.position_fields.items():
            if field not in position:
                position[field] = default_value if field != 'entry_price' else current_price
        return position

    def execute_trades(self, state: MarketState) -> MarketState:
        """Execute trades based on the trading plan"""
        try:
            # Initialize positions if not exists
            if 'positions' not in state:
                state['positions'] = {}
            
            # Ensure all existing positions have required fields
            for symbol, position in state['positions'].items():
                if symbol in state['current_prices']:
                    state['positions'][symbol] = self._ensure_position_fields(position, state['current_prices'][symbol])
            
            # Validate required state fields
            required_fields = [
                'market_analysis', 'risk_assessment', 'financial_advice',
                'risk_analysis', 'trading_plan'
            ]
            missing_fields = [field for field in required_fields if field not in state or not state[field]]
            
            if missing_fields:
                print(f"Warning: Missing required state fields: {', '.join(missing_fields)}")
                print("Please ensure you have called the following methods in order:")
                print("1. analyze_market()")
                print("2. assess_risk()")
                print("3. get_financial_advice()")
                print("4. analyze_risk()")
                print("5. create_trading_plan()")
                return state
            
            print("Proceeding with trade execution...")
            
            # Get trade execution instructions
            execution_instructions = self._rate_limited_invoke(
                self.executor_chain,
                {
                    'trading_plan': state['trading_plan'],
                    'current_prices': state['current_prices'],
                    'positions': state['positions'],
                    'available_balance': state['available_balance']
                }
            )
            
            # Clean up the response
            execution_instructions = execution_instructions.strip()
            
            # Remove any markdown code block markers
            execution_instructions = execution_instructions.replace('```json', '').replace('```', '')
            
            # Remove "Assistant:" prefix if present
            if execution_instructions.startswith('Assistant:'):
                execution_instructions = execution_instructions[10:].strip()
            
            # Extract JSON array from the response
            json_match = re.search(r'\[\s*\{.*\}\s*\]', execution_instructions, re.DOTALL)
            if json_match:
                execution_instructions = json_match.group(0)
            else:
                # If no JSON array found, try to find individual JSON objects
                json_objects = re.findall(r'\{[^{}]*\}', execution_instructions)
                if json_objects:
                    # Filter out information objects and only keep trade objects
                    trade_objects = [
                        obj for obj in json_objects 
                        if '"type":' in obj and '"type": "information"' not in obj
                    ]
                    if trade_objects:
                        execution_instructions = '[' + ','.join(trade_objects) + ']'
                    else:
                        raise ValueError("No valid trade objects found in response")
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Try to parse the JSON
            try:
                trades = json.loads(execution_instructions)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to fix fractions and parse again
                fixed_json = fix_json_fractions(execution_instructions)
                trades = json.loads(fixed_json)
                print("Successfully parsed JSON after fixing fractions")
            
            # Define valid trading pairs
            valid_pairs = [
                # Major cryptocurrencies
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT',
                # Meme coins
                'PEPEUSDT', 'FLOKIUSDT', 'BONKUSDT', 'BOMEUSDT', 'WIFUSDT',
                # DeFi tokens
                'UNIUSDT', 'CAKEUSDT', 'SUSHIUSDT', 'COMPUSDT', 'AAVEUSDT', 'MKRUSDT', 'YFIUSDT', 'CRVUSDT',
                'SNXUSDT', 'PERPUSDT', 'GMXUSDT', 'BALUSDT', 'SUSHIUSDT', '1INCHUSDT', 'ZRXUSDT',
                # Layer 1s
                'AVAXUSDT', 'MATICUSDT', 'DOTUSDT', 'LINKUSDT',
                # Other popular tokens
                'SHIBUSDT', 'LTCUSDT', 'ATOMUSDT', 'NEARUSDT', 'ALGOUSDT'
            ]
            
            # Validate each trade and update portfolio
            valid_trades = []
            for trade in trades:
                try:
                    if not isinstance(trade, dict):
                        print(f"Invalid trade format: {trade}")
                        continue
                    
                    # Skip information objects
                    if trade.get('type') == 'information':
                        continue
                        
                    if all(key in trade for key in ['type', 'symbol', 'amount', 'reason']):
                        if trade['type'].lower() in ['buy', 'sell']:
                            # Check if trying to trade USDT directly
                            if trade['symbol'] == 'USDT':
                                print(f"Invalid trade: Cannot trade USDT directly. To convert to USDT, sell the cryptocurrency. To convert from USDT, buy the cryptocurrency.")
                                continue
                                
                            if trade['symbol'] in valid_pairs and trade['symbol'] in state['current_prices']:
                                # Convert amount to float if it's a string
                                try:
                                    amount = float(trade['amount']) if isinstance(trade['amount'], str) else trade['amount']
                                    if amount > 0:
                                        # Update the trade with the converted amount
                                        trade['amount'] = amount
                                        
                                        # Calculate trade value in USDT
                                        price = state['current_prices'][trade['symbol']]
                                        trade_value = amount * price
                                        
                                        # Update portfolio based on trade type
                                        if trade['type'].lower() == 'buy':
                                            # Check if we have enough USDT
                                            if trade_value > state['available_balance']:
                                                print(f"Skipping trade: Insufficient USDT balance. Required: {trade_value}, Available: {state['available_balance']}")
                                                continue
                                            
                                            # Update available balance
                                            state['available_balance'] -= trade_value
                                            
                                            # Update or create position
                                            if trade['symbol'] not in state['positions']:
                                                state['positions'][trade['symbol']] = {
                                                    'amount': amount,
                                                    'average_price': price,
                                                    'total_value': trade_value,
                                                    'entry_price': price  # Add entry price for new positions
                                                }
                                            else:
                                                current_position = state['positions'][trade['symbol']]
                                                total_amount = current_position['amount'] + amount
                                                total_value = current_position['total_value'] + trade_value
                                                state['positions'][trade['symbol']] = {
                                                    'amount': total_amount,
                                                    'average_price': total_value / total_amount,
                                                    'total_value': total_value,
                                                    'entry_price': current_position.get('entry_price', price)  # Keep original entry price
                                                }
                                            
                                        else:  # sell
                                            # Check if we have enough of the asset
                                            if trade['symbol'] not in state['positions']:
                                                print(f"Skipping trade: No position in {trade['symbol']}")
                                                continue
                                                
                                            current_position = state['positions'][trade['symbol']]
                                            if current_position['amount'] < amount:
                                                print(f"Skipping trade: Insufficient {trade['symbol']} balance. Required: {amount}, Available: {current_position['amount']}")
                                                continue
                                            
                                            # Calculate remaining position
                                            remaining_amount = current_position['amount'] - amount
                                            remaining_value = remaining_amount * price  # Use current price for remaining value
                                            
                                            if remaining_amount <= 0:
                                                # Remove position if fully sold
                                                del state['positions'][trade['symbol']]
                                            else:
                                                state['positions'][trade['symbol']] = {
                                                    'amount': remaining_amount,
                                                    'average_price': price,  # Use current price as new average
                                                    'total_value': remaining_value,
                                                    'entry_price': current_position.get('entry_price', price)  # Keep original entry price
                                                }
                                            
                                            # Update available balance
                                            state['available_balance'] += trade_value
                                        
                                        # Add trade to valid trades
                                        valid_trades.append(trade)
                                        print(f"Executed {trade['type']} trade: {amount} {trade['symbol']} at {price} USDT (Total: {trade_value} USDT)")
                                        
                                    else:
                                        print(f"Invalid amount in trade: {trade} (amount must be greater than 0)")
                                except (ValueError, TypeError) as e:
                                    print(f"Invalid amount format in trade: {trade} (amount must be a valid number)")
                                    print(f"Error details: {str(e)}")
                                except Exception as e:
                                    print(f"Error processing trade: {str(e)}")
                                    print(f"Trade data: {trade}")
                            else:
                                print(f"Invalid symbol in trade: {trade} (must be one of {valid_pairs})")
                        else:
                            print(f"Invalid trade type: {trade}")
                    else:
                        print(f"Missing required fields in trade: {trade}")
                except Exception as e:
                    print(f"Error validating trade: {str(e)}")
                    print(f"Trade data: {trade}")
            
            # Update portfolio value
            try:
                portfolio_value = state['available_balance']
                for symbol, position in state['positions'].items():
                    if symbol in state['current_prices']:
                        current_price = state['current_prices'][symbol]
                        # Ensure position has all required fields
                        position = self._ensure_position_fields(position, current_price)
                        position_value = position['amount'] * current_price
                        portfolio_value += position_value
                        # Update position values
                        position['total_value'] = position_value
                        position['average_price'] = current_price
                        if position['entry_price'] == 0:
                            position['entry_price'] = current_price
                state['portfolio_value'] = portfolio_value
            except Exception as e:
                print(f"Error updating portfolio value: {str(e)}")
                # Set a default value if calculation fails
                state['portfolio_value'] = state['available_balance']
            
            state['executed_trades'] = valid_trades
            
            print(f"\nPortfolio Update:")
            print(f"Available Balance: {state['available_balance']} USDT")
            print(f"Portfolio Value: {state['portfolio_value']} USDT")
            print("Current Positions:")
            for symbol, position in state['positions'].items():
                try:
                    current_price = state['current_prices'][symbol]
                    # Ensure position has all required fields
                    position = self._ensure_position_fields(position, current_price)
                    position_value = position['amount'] * current_price
                    print(f"- {symbol}: {position['amount']} (Value: {position_value} USDT, Entry: {position['entry_price']} USDT)")
                except Exception as e:
                    print(f"- {symbol}: {position['amount']} (Error calculating value: {str(e)})")
            
        except Exception as e:
            print(f"Error in trade execution: {str(e)}")
            print(f"Raw instructions: {execution_instructions}")
            
            # Try to fix JSON parsing for fractions
            try:
                if isinstance(execution_instructions, str):
                    fixed_json = fix_json_fractions(execution_instructions)
                    trades = json.loads(fixed_json)
                    print("Successfully parsed JSON after fixing fractions")
                    return self.execute_trades(state)  # Retry with fixed JSON
            except Exception as e2:
                print(f"Error fixing JSON: {str(e2)}")
        
        return state

    def save_state(self, state: MarketState, filename: str = 'trading_state.json'):
        """Save the current trading state to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"Trading state saved to {filename}")
        except Exception as e:
            print(f"Error saving trading state: {str(e)}")

    def load_state(self, filename: str = 'trading_state.json') -> MarketState:
        """Load a previously saved trading state"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            print(f"Trading state loaded from {filename}")
            return state
        except FileNotFoundError:
            print(f"No saved state found at {filename}")
            return None
        except Exception as e:
            print(f"Error loading trading state: {str(e)}")
            return None

    def run_trading_workflow(self, state: MarketState) -> MarketState:
        """Run the complete trading workflow in the correct sequence"""
        print(f"Starting trading workflow with {self.personality.name}...")
        
        # Step 1: Market Analysis
        print("1. Analyzing market...")
        state = self.analyze_market(state)
        self.save_state(state)  # Save after each step
        
        # Step 2: Risk Assessment
        print("2. Assessing risks...")
        state = self.assess_risk(state)
        self.save_state(state)
        
        # Step 3: Financial Advice
        print("3. Getting financial advice...")
        state = self.get_financial_advice(state)
        self.save_state(state)
        
        # Step 4: Risk Analysis
        print("4. Performing detailed risk analysis...")
        state = self.analyze_risk(state)
        self.save_state(state)
        
        # Step 5: Create Trading Plan
        print("5. Creating trading plan...")
        state = self.create_trading_plan(state)
        self.save_state(state)
        
        # Step 6: Execute Trades
        print("6. Executing trades...")
        state = self.execute_trades(state)
        self.save_state(state)
        
        return state 