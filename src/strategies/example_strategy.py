"""
🌙 Moon Dev's Example Strategy
This is a template for creating custom strategies
"""

from .base_strategy import BaseStrategy
from src.config import MONITORED_TOKENS
import pandas as pd
from termcolor import cprint

class ExampleMeanReversionStrategy(BaseStrategy):
    def __init__(self):
        """Initialize the strategy"""
        super().__init__("Example Mean Reversion")
        self.lookback_periods = 20
        
    def generate_signals(self) -> dict:
        """Generate trading signals based on mean reversion"""
        try:
            # This is just an example - replace with your own logic!
            for token in MONITORED_TOKENS:
                # Get market data (implement your own data collection)
                data = self._get_market_data(token)
                if data is None:
                    continue
                    
                # Calculate indicators
                mean_price = data['close'].rolling(self.lookback_periods).mean()
                std_dev = data['close'].rolling(self.lookback_periods).std()
                current_price = data['close'].iloc[-1]
                
                # Calculate z-score
                z_score = (current_price - mean_price.iloc[-1]) / std_dev.iloc[-1]
                
                # Generate signal based on z-score
                if z_score < -2:  # Oversold
                    signal_strength = min(abs(z_score) / 4, 1)  # Normalize to 0-1
                    signal = {
                        'token': token,
                        'signal': signal_strength,
                        'direction': 'BUY',
                        'metadata': {
                            'strategy_type': 'mean_reversion',
                            'z_score': float(z_score),
                            'current_price': float(current_price),
                            'mean_price': float(mean_price.iloc[-1]),
                            'std_dev': float(std_dev.iloc[-1])
                        }
                    }
                elif z_score > 2:  # Overbought
                    signal_strength = min(abs(z_score) / 4, 1)
                    signal = {
                        'token': token,
                        'signal': signal_strength,
                        'direction': 'SELL',
                        'metadata': {
                            'strategy_type': 'mean_reversion',
                            'z_score': float(z_score),
                            'current_price': float(current_price),
                            'mean_price': float(mean_price.iloc[-1]),
                            'std_dev': float(std_dev.iloc[-1])
                        }
                    }
                else:
                    signal = {
                        'token': token,
                        'signal': 0,
                        'direction': 'NEUTRAL',
                        'metadata': {
                            'strategy_type': 'mean_reversion',
                            'z_score': float(z_score)
                        }
                    }
                
                # Validate and format signal
                if self.validate_signal(signal):
                    signal['metadata'] = self.format_metadata(signal['metadata'])
                    return signal
                    
            return None
            
        except Exception as e:
            cprint(f"❌ Error generating signals: {str(e)}", "red")
            return None
            
    def _get_market_data(self, token: str) -> pd.DataFrame:
        """
        Get market data for analysis
        This is just a placeholder - implement your own data collection!
        """
        try:
            # Implement your data collection logic here
            # Should return DataFrame with OHLCV data
            return pd.DataFrame()  # Placeholder
        except Exception as e:
            cprint(f"❌ Error getting market data: {str(e)}", "red")
            return None 