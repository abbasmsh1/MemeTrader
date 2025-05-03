from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Binance client
client = Client(
    os.getenv('BINANCE_API_KEY'),
    os.getenv('BINANCE_API_SECRET')
)

# Test pairs
test_pairs = [
    'DOGEUSDT',    # Dogecoin
    'SHIBUSDT',    # Shiba Inu
    'PEPEUSDT',    # Pepe
    'FLOKIUSDT',   # Floki Inu
    'BONKUSDT',    # Bonk
    'WIFUSDT',     # dogwifhat
    'MYROUSDT',    # Myro
    'BOMEUSDT',    # Book of Meme
    '1000FLOKIUSDT', # 1000Floki
    'SAMOUSDT',    # Samoyedcoin
    'ELONUSDT',    # Dogelon Mars
    'HOGEUSDT',    # Hoge Finance
    'KISHUUSDT',   # Kishu Inu
    'SAFEMOONUSDT', # SafeMoon
    'MOONUSDT'     # Mooncoin
]

print("Testing trading pairs...")
working_pairs = []

for pair in test_pairs:
    try:
        # Try to get the ticker price
        ticker = client.get_symbol_ticker(symbol=pair)
        print(f"✅ {pair} is available")
        working_pairs.append(pair)
    except BinanceAPIException as e:
        print(f"❌ {pair} is not available: {str(e)}")

print("\nWorking pairs:")
for pair in working_pairs:
    print(f"- {pair}") 