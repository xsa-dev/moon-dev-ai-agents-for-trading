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
        """Get open interest data from local file"""
        try:
            filepath = PROJECT_ROOT / "src" / "data" / "oi_history.csv"
            if not filepath.exists():
                print("❌ OI history file not found")
                return None
                
            df = pd.read_csv(filepath)
            if df is not None and not df.empty:
                print(f"✨ Successfully loaded {len(df)} OI records!")
                return df
            else:
                print("❌ No data in OI history file")
                return None
                
        except Exception as e:
            print(f"💥 Error loading OI data: {str(e)}")
            return None
