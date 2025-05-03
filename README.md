# MemeTrader AI

An AI-powered trading system that uses CrewAI and the Binance API to analyze and trade meme coins. The system operates with a simulated wallet starting with $20, aiming to reach $100 by the end of the week.

## Features

- Multiple AI agents working together:
  - Market Analyst: Analyzes meme coin trends and patterns
  - Risk Manager: Manages trading risks and portfolio balance
  - Trader: Executes trades based on analysis and risk assessment
- Simulated trading environment
- Real-time market data analysis
- Risk management and portfolio optimization

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Binance API credentials:
```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

3. Run the trading system:
```bash
python main.py
```

## Project Structure

- `agents/`: Contains the AI agent definitions
- `config/`: Configuration files and constants
- `utils/`: Utility functions and helpers
- `main.py`: Main execution script
- `requirements.txt`: Project dependencies

## Disclaimer

This is a simulated trading system for educational purposes only. Always do your own research before making any real trading decisions. 