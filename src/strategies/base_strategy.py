"""
🌙 Moon Dev's Base Strategy Class
All custom strategies must inherit from this class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from termcolor import cprint

class BaseStrategy(ABC):
    def __init__(self, name: str):
        """Initialize the strategy"""
        self.name = name
        cprint(f"🚀 Initializing {self.name} strategy...", "white", "on_blue")
    
    @abstractmethod
    def generate_signals(self) -> Dict[str, Any]:
        """
        Generate trading signals for the strategy.
        
        Must return a dictionary with:
        {
            'token': str,          # Token address
            'signal': float,       # Signal strength (0-1)
            'direction': str,      # 'BUY', 'SELL', or 'NEUTRAL'
            'metadata': dict       # Strategy-specific data
        }
        """
        pass
    
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate that a signal has all required fields"""
        required_fields = ['token', 'signal', 'direction']
        
        # Check required fields exist
        for field in required_fields:
            if field not in signal:
                cprint(f"❌ Missing required field: {field}", "red")
                return False
        
        # Validate signal strength is between 0 and 1
        if not 0 <= signal['signal'] <= 1:
            cprint("❌ Signal strength must be between 0 and 1", "red")
            return False
            
        # Validate direction is valid
        if signal['direction'] not in ['BUY', 'SELL', 'NEUTRAL']:
            cprint("❌ Direction must be 'BUY', 'SELL', or 'NEUTRAL'", "red")
            return False
            
        return True
    
    def format_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format metadata to include strategy name and timestamp"""
        from datetime import datetime
        
        if not metadata:
            metadata = {}
            
        metadata.update({
            'strategy_name': self.name,
            'timestamp': datetime.now().isoformat()
        })
        
        return metadata 