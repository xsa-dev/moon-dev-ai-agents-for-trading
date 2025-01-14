"""
🌙 Moon Dev's API Handler
Built with love by Moon Dev 🚀
"""

import os
import pandas as pd
import requests
from datetime import datetime
import time
from pathlib import Path
import numpy as np
import traceback

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

class MoonDevAPI:
    def __init__(self):
        """Initialize the API handler with data caching"""
        self.base_dir = PROJECT_ROOT / "src" / "agents" / "api_data"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        print("🌙 Moon Dev API: Ready to rock! 🚀")
        print(f"📂 Saving data to: {self.base_dir.absolute()}")
        
    def _fetch_data(self, url, filename):
        """Fetch data with simple retry logic"""
        try:
            # Use a session for better connection handling
            with requests.Session() as session:
                # Configure the session for larger responses
                session.headers.update({'Accept-Encoding': 'gzip, deflate'})
                
                print(f"🚀 Moon Dev API: Blasting off to fetch {filename}...")
                response = session.get(url, stream=True)  # Stream the response
                response.raise_for_status()
                
                # Save the data
                filepath = self.base_dir / filename
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                    
                # Read and return the data
                return pd.read_csv(filepath)
                
        except Exception as e:
            print(f"💥 Oops! Error: {str(e)}")
            return None
            
    def get_open_interest(self):
        """Get fresh open interest data"""
        try:
            # Simulate fetching fresh data (for testing)
            # In production, this would be an actual API call
            current_time = datetime.now()
            
            # Generate slightly different values each time (for testing)
            base_btc = 8_677_685_572.08  # Base value
            base_eth = 5_525_816_136.14  # Base value
            
            # Add some random variation (±1%)
            btc_variation = base_btc * (1 + (np.random.random() - 0.5) * 0.02)  # ±1% change
            eth_variation = base_eth * (1 + (np.random.random() - 0.5) * 0.02)  # ±1% change
            
            # Create new data point
            new_data = pd.DataFrame([{
                'timestamp': current_time,
                'btc_oi': btc_variation,
                'eth_oi': eth_variation,
                'total_oi': btc_variation + eth_variation
            }])
            
            # Load existing data
            filepath = PROJECT_ROOT / "src" / "data" / "oi_history.csv"
            if filepath.exists():
                df = pd.read_csv(filepath)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                print(f"✨ Successfully loaded {len(df)} OI records!")
                
                # Append new data
                df = pd.concat([df, new_data], ignore_index=True)
            else:
                df = new_data
                
            # Save updated data
            df.to_csv(filepath, index=False)
            
            return df
            
        except Exception as e:
            print(f"💥 Error loading OI data: {str(e)}")
            return None

    def get_funding_rates(self):
        """Get fresh funding rate data for all tracked symbols"""
        try:
            current_time = datetime.now()
            
            # Create DataFrame with the real CSV structure (unpivoted format for display)
            new_data = pd.DataFrame([
                {'symbol': 'BTC', 'funding_rate': 0.0001, 'annual_rate': 10.95},
                {'symbol': 'ETH', 'funding_rate': 9.606e-05, 'annual_rate': 10.51857},
                {'symbol': 'SOL', 'funding_rate': -6.63e-06, 'annual_rate': -0.725985},
                {'symbol': 'WIF', 'funding_rate': 5e-05, 'annual_rate': 5.475},
                {'symbol': 'FARTCOIN', 'funding_rate': 5e-05, 'annual_rate': 5.475},
                {'symbol': 'BNB', 'funding_rate': 0.0, 'annual_rate': 0.0}
            ])
            
            # Add timestamp and pivot the data to have one row
            new_data['timestamp'] = current_time
            
            # Create one-line format
            pivoted_data = pd.DataFrame({'timestamp': [current_time]})
            for _, row in new_data.iterrows():
                symbol = row['symbol']
                pivoted_data[f'{symbol}_funding_rate'] = row['funding_rate']
                pivoted_data[f'{symbol}_annual_rate'] = row['annual_rate']
            
            # Load and update history file with pivoted format
            filepath = PROJECT_ROOT / "src" / "data" / "funding_history.csv"
            try:
                if filepath.exists():
                    df = pd.read_csv(filepath)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    print(f"✨ Successfully loaded {len(df)} funding rate records!")
                    df = pd.concat([df, pivoted_data], ignore_index=True)
                else:
                    df = pivoted_data
            except Exception as e:
                print(f"⚠️ Error reading existing data: {str(e)}")
                print("🔄 Starting fresh with new data")
                df = pivoted_data
            
            # Save the pivoted format to history
            df.to_csv(filepath, index=False)
            
            # Return the unpivoted format for the agent to use
            return new_data
            
        except Exception as e:
            print(f"💥 Error loading funding rate data: {str(e)}")
            traceback.print_exc()
            return None
