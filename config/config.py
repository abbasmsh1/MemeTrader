from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Binance API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Together AI Configuration
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
TOGETHER_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # Updated model identifier

# Trading Configuration
INITIAL_BALANCE = 20.0  # Initial balance in USD
TARGET_BALANCE = 100.0  # Target balance in USD
MAX_RISK_PER_TRADE = 0.1  # Maximum 10% of portfolio per trade
STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
TAKE_PROFIT_PERCENTAGE = 0.15  # 15% take profit
MIN_PURCHASE_AMOUNT = 5.0  # Minimum purchase amount in USD

# Cryptocurrency Configuration
MAJOR_COINS = [
    'BTCUSDT',     # Bitcoin
    'ETHUSDT',     # Ethereum
    'BNBUSDT',     # Binance Coin
    'SOLUSDT',     # Solana
    'ADAUSDT',     # Cardano
    'XRPUSDT',     # Ripple
    'DOTUSDT',     # Polkadot
    'AVAXUSDT',    # Avalanche
    'MATICUSDT',   # Polygon
    'LINKUSDT'     # Chainlink
]

MEME_COINS = [
    'DOGEUSDT',    # Dogecoin
    'SHIBUSDT',    # Shiba Inu
    'PEPEUSDT',    # Pepe
    'FLOKIUSDT',   # Floki Inu
    'BONKUSDT',    # Bonk
    'WIFUSDT',     # dogwifhat
    'BOMEUSDT'     # Book of Meme
]

DEFI_COINS = [
    'UNIUSDT',     # Uniswap
    'AAVEUSDT',    # Aave
    'CAKEUSDT',    # PancakeSwap
    'SUSHIUSDT',   # SushiSwap
    'COMPUSDT',    # Compound
    'MKRUSDT',     # Maker
    'SNXUSDT',     # Synthetix
    'YFIUSDT',     # Yearn.Finance
    'CRVUSDT',     # Curve DAO
    'BALUSDT'      # Balancer
]

# Combine all coins for trading
TRADING_COINS = MAJOR_COINS + MEME_COINS + DEFI_COINS

# Time Configuration
TRADING_INTERVAL = 10  # Trading interval in seconds
MAX_TRADES_PER_DAY = 5000  # Maximum number of trades per day

# Agent Configuration
AGENT_TEMPERATURE = 0.7  # Temperature for agent responses
AGENT_MODEL = TOGETHER_MODEL 