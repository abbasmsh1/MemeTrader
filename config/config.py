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
INITIAL_BALANCE = 20  # Starting balance in USDT
TARGET_BALANCE = 100000  # Target balance in USDT (100x growth)
MAX_RISK_PER_TRADE = 0.1  # Maximum 10% of portfolio per trade
STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
TAKE_PROFIT_PERCENTAGE = 0.15  # 15% take profit
MIN_PURCHASE_AMOUNT = 5.0  # Minimum purchase amount in USD

# Cryptocurrency Configuration
MAJOR_COINS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT'
]

MEME_COINS = [
    'PEPEUSDT', 'FLOKIUSDT', 'BONKUSDT', 'BOMEUSDT', 'WIFUSDT'
]

DEFI_COINS = [
    'UNIUSDT', 'CAKEUSDT', 'SUSHIUSDT', 'COMPUSDT', 'AAVEUSDT', 'MKRUSDT', 'YFIUSDT', 'CRVUSDT',
    'SNXUSDT', 'PERPUSDT', 'GMXUSDT', 'BALUSDT', '1INCHUSDT', 'ZRXUSDT'
]

# Combine all trading pairs
TRADING_COINS = MAJOR_COINS + MEME_COINS + DEFI_COINS

# Time Configuration
TRADING_INTERVAL = 10  # Trading interval in seconds
MAX_TRADES_PER_DAY = 5000  # Maximum number of trades per day

# Agent Configuration
AGENT_TEMPERATURE = 0.7
AGENT_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1" 