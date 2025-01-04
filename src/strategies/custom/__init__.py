"""
🌙 Moon Dev's Custom Strategies Package
This package will automatically discover and load custom strategies
"""

import os
import importlib
import inspect
from ..base_strategy import BaseStrategy
from termcolor import cprint

def load_custom_strategies():
    """Dynamically load all custom strategy classes"""
    strategies = {}
    
    # Get the directory containing custom strategies
    custom_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List all Python files in the directory
    for filename in os.listdir(custom_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove .py extension
            
            try:
                # Import the module
                module = importlib.import_module(f'.{module_name}', package=__package__)
                
                # Find all classes that inherit from BaseStrategy
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseStrategy) and 
                        obj != BaseStrategy):
                        strategies[name] = obj
                        cprint(f"✨ Loaded custom strategy: {name}", "white", "on_green")
                        
            except Exception as e:
                cprint(f"❌ Error loading {module_name}: {str(e)}", "red")
                
    return strategies

# Export the loader function
__all__ = ['load_custom_strategies'] 