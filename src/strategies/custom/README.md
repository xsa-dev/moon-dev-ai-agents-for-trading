# 🌙 Moon Dev's Custom Strategies Directory

This directory is for your private trading strategies. Any strategy files placed here will be automatically discovered and loaded by the trading agent.

## Creating a Custom Strategy

1. Create a new Python file in this directory (e.g., `my_strategy.py`)
2. Import and inherit from the base strategy class:
```python
from ..base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Strategy Name")
        # Your initialization code here
    
    def generate_signals(self) -> dict:
        # Your strategy logic here
        return {
            'token': 'token_address',
            'signal': 0.85,        # 0-1 strength
            'direction': 'BUY',    # 'BUY', 'SELL', or 'NEUTRAL'
            'metadata': {
                'your_custom_data': 'here'
            }
        }
```

## Required Signal Format
- `token`: Token address (string)
- `signal`: Signal strength between 0-1 (float)
- `direction`: Must be 'BUY', 'SELL', or 'NEUTRAL' (string)
- `metadata`: Optional dictionary with strategy-specific data

## Example Metadata Fields
```python
metadata = {
    'strategy_type': 'mean_reversion',
    'indicators': {
        'rsi': 28,
        'macd': 'bullish',
        'volume': 'above_average'
    },
    'confidence_factors': {
        'price_action': True,
        'volume_confirms': True
    },
    'analysis': {
        'support_level': 1.23,
        'resistance_level': 1.45
    }
}
```

## Tips
- Keep your strategies in this directory private
- Use the example strategy as a template
- Implement proper error handling
- Add detailed metadata for better LLM analysis
- Use Moon Dev's utility functions from nice_funcs.py

## Security
- Add this directory to .gitignore to keep your strategies private
- Never commit API keys or private keys
- Use environment variables for sensitive data

## Questions?
Check out the example strategy or reach out to Moon Dev for help! 🚀 