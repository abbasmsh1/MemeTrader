import json
import time
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
    financial_advice: str
    risk_analysis: str

class TradingAgents:
    def __init__(self, strategy: str = 'conservative'):
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
                DeFi tokens: UNIUSDT, CAKEUSDT, SUSHIUSDT, COMPUSDT, AAVEUSDT, MKRUSDT
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
                    "symbol": "BTCUSDT" or "ETHUSDT" or "BNBUSDT" or "SOLUSDT" or "ADAUSDT" or "XRPUSDT" or "DOGEUSDT" or "PEPEUSDT" or "FLOKIUSDT" or "BONKUSDT" or "BOMEUSDT" or "WIFUSDT" or "UNIUSDT" or "CAKEUSDT" or "SUSHIUSDT" or "COMPUSDT" or "AAVEUSDT" or "MKRUSDT" or "AVAXUSDT" or "MATICUSDT" or "DOTUSDT" or "LINKUSDT" or "SHIBUSDT" or "LTCUSDT" or "ATOMUSDT" or "NEARUSDT" or "ALGOUSDT",
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
        """Helper method to handle rate limiting and retries"""
        for attempt in range(max_retries):
            try:
                # Ensure we're not exceeding rate limits
                current_time = time.time()
                time_since_last_request = current_time - self.last_request_time
                if time_since_last_request < self.min_request_interval:
                    wait_time = self.min_request_interval - time_since_last_request
                    print(f"Rate limiting: waiting {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                
                # Make the request
                result = chain.invoke(input_data)
                self.last_request_time = time.time()
                return result
                
            except ValueError as e:
                error_str = str(e)
                if "rate_limit" in error_str and attempt < max_retries - 1:
                    # If we hit a rate limit, wait longer and try again
                    wait_time = (attempt + 1) * 10  # Increased backoff time to 10 seconds
                    print(f"Rate limit hit, waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                raise e
            except Exception as e:
                raise e
    
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
    
    def execute_trades(self, state: MarketState) -> MarketState:
        """Execute trades based on the trading plan"""
        try:
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
            import re
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
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {str(e)}")
                print(f"Raw instructions: {execution_instructions}")
                # Try to fix common JSON issues
                execution_instructions = execution_instructions.replace("'", '"')  # Replace single quotes with double quotes
                execution_instructions = execution_instructions.replace('None', 'null')  # Replace Python None with JSON null
                execution_instructions = execution_instructions.replace('True', 'true')  # Replace Python True with JSON true
                execution_instructions = execution_instructions.replace('False', 'false')  # Replace Python False with JSON false
                # Remove any extra whitespace or newlines
                execution_instructions = re.sub(r'\s+', ' ', execution_instructions)
                trades = json.loads(execution_instructions)
            
            # Define valid trading pairs
            valid_pairs = [
                # Major cryptocurrencies
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT',
                # Meme coins
                'PEPEUSDT', 'FLOKIUSDT', 'BONKUSDT', 'BOMEUSDT', 'WIFUSDT',
                # DeFi tokens
                'UNIUSDT', 'CAKEUSDT', 'SUSHIUSDT', 'COMPUSDT', 'AAVEUSDT', 'MKRUSDT',
                # Layer 1s
                'AVAXUSDT', 'MATICUSDT', 'DOTUSDT', 'LINKUSDT',
                # Other popular tokens
                'SHIBUSDT', 'LTCUSDT', 'ATOMUSDT', 'NEARUSDT', 'ALGOUSDT'
            ]
            
            # Validate each trade
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
                                        valid_trades.append(trade)
                                    else:
                                        print(f"Invalid amount in trade: {trade} (amount must be greater than 0)")
                                except (ValueError, TypeError):
                                    print(f"Invalid amount format in trade: {trade} (amount must be a valid number)")
                            else:
                                print(f"Invalid symbol in trade: {trade} (must be one of {valid_pairs})")
                        else:
                            print(f"Invalid trade type: {trade}")
                    else:
                        print(f"Missing required fields in trade: {trade}")
                except Exception as e:
                    print(f"Error validating trade: {str(e)}")
                    print(f"Trade data: {trade}")
            
            state['executed_trades'] = valid_trades
            
        except Exception as e:
            print(f"Error in trade execution: {str(e)}")
            print(f"Raw instructions: {execution_instructions}")
        
        return state 