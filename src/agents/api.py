"""
Moon Dev Market Data API Interface 🌙
Provides access to market data and copybot functionality
"""

import requests
import pandas as pd
import io
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from termcolor import colored
import time
load_dotenv()

class MoonDevAPI:
    """Base API client for Moon Dev services 🌙"""
    def __init__(self):
        self.base_url = 'http://api.moondev.com:8000'
        self.headers = {'X-API-Key': os.getenv('MOONDEV_API_KEY')}
        self.save_dir = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/agents/api_data'
        os.makedirs(self.save_dir, exist_ok=True)
        print(colored("🌙 Moon Dev API: Ready to rock! 🚀", "white", "on_blue", attrs=["bold"]))
        print(colored(f"📂 Saving data to: {self.save_dir}", "white", "on_blue"))

    def _get_dataframe(self, endpoint, save_file=True):
        """Generic method to fetch and convert API response to DataFrame"""
        try:
            # Handle different endpoint types
            if endpoint.startswith('copybot'):
                url = f'{self.base_url}/{endpoint}'
                filename = 'follow_list.csv' if 'follow_list' in endpoint else 'recent_txs.csv'
            else:
                url = f'{self.base_url}/files/{endpoint}'
                filename = endpoint.split('?')[0]  # Remove query params
            
            print(colored(f"🚀 Moon Dev API: Blasting off to fetch {endpoint}...", "white", "on_blue"))
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            df = pd.read_csv(io.StringIO(response.text))
            
            if save_file:
                save_path = os.path.join(self.save_dir, filename)
                df.to_csv(save_path, index=False)
                print(colored(f"💾 Data saved successfully to {filename}!", "white", "on_blue"))
            
            return df
        except Exception as e:
            print(colored(f"💥 Oops! Error: {e}", "white", "on_red"))
            return None

    # Market Data Methods
    def get_liq_data(self, symbol=None, limit=100000):
        """Get liquidation data with optional symbol filtering"""
        try:
            df = self._get_dataframe(f'liq_data.csv?limit={limit}')
            if df is None:
                return None

            if symbol:
                # Since there are no column headers, use iloc to filter by first column
                df = df[df.iloc[:, 0] == symbol]
                print(colored(f"🎯 Found some juicy liquidations for {symbol}!", "white", "on_blue"))
            
            print(colored("💦 Latest liquidation data (courtesy of Moon Dev):", "white", "on_blue"))
            if len(df) > 0:
                print(df.tail())
            else:
                print("No matching data found")
            return df
        except Exception as e:
            print(f"❌ Error processing liquidation data: {e}")
            return None

    def get_funding_rate(self, symbol=None):
        """Get funding rate data with optional symbol filtering"""
        try:
            df = self._get_dataframe('funding.csv')
            if df is None:
                return None

            if symbol:
                # Use iloc for filtering without column headers
                df = df[df.iloc[:, 0] == symbol]
                print(f"💰 Filtered funding rate data for {symbol}")
            
            print("💸 Recent funding rate data:")
            if len(df) > 0:
                print(df.tail())
            else:
                print("No matching data found")
            return df
        except Exception as e:
            print(f"❌ Error processing funding rate data: {e}")
            return None

    def get_open_interest(self, symbol=None, total=False):
        """Get open interest data with optional symbol filtering"""
        try:
            file_name = 'oi_total.csv' if total else 'oi.csv'
            df = self._get_dataframe(file_name)
            if df is None:
                return None

            if symbol and not total:
                # Use iloc for filtering without column headers
                df = df[df.iloc[:, 1] == symbol]  # Symbol in second column for OI
                print(f"📊 Filtered OI data for {symbol}")
            
            print("📈 Recent open interest data:")
            if len(df) > 0:
                print(df.tail())
            else:
                print("No matching data found")
            return df
        except Exception as e:
            print(f"❌ Error processing open interest data: {e}")
            return None

    def get_new_token_addresses(self):
        """Get the latest token launches"""
        try:
            df = self._get_dataframe('new_token_addresses.csv')
            print("🆕 Moon Dev New Token Launches loaded!")
            if len(df) > 0:
                print(df.tail())
            else:
                print("No new token launches found")
            return df
        except Exception as e:
            print(f"❌ Error getting new token addresses: {e}")
            return None

    # CopyBot Methods
    def get_copybot_follow_list(self):
        """Get the current follow list for copy trading"""
        try:
            df = self._get_dataframe('copybot/data/follow_list')
            print("👥 Moon Dev CopyBot follow list loaded!")
            print(df.tail())
            return df
        except Exception as e:
            print(f"❌ Error getting follow list: {e}")
            return None

    def get_recent_transactions(self):
        """Get recent transactions from copy trading"""
        try:
            df = self._get_dataframe('copybot/data/recent_txs')
            print("🔄 Moon Dev CopyBot recent transactions loaded!")
            print(df.tail())
            return df
        except Exception as e:
            print(f"❌ Error getting recent transactions: {e}")
            return None

    def list_available_files(self):
        """List all available CSV files"""
        try:
            response = requests.get(f'{self.base_url}/list-csvs', headers=self.headers)
            response.raise_for_status()
            
            # Combine API files with copybot files
            files = response.json()
            copybot_files = ['follow_list.csv', 'recent_txs.csv']
            all_files = sorted(set(files + copybot_files))  # Remove duplicates
            
            print("📁 Available files:")
            for file in all_files:
                print(f"  - {file}")
            return all_files
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return None

# Example usage
if __name__ == "__main__":
    api = MoonDevAPI()
    symbol = "BTC"

    print("\n" + "="*70)
    print(colored("🌙  Moon Dev Market Data API Test  🌙", "white", on_color="on_magenta", attrs=["bold"]))
    print("="*70 + "\n")

    # Test market data endpoints
    print(colored("📊  MARKET DATA ENDPOINTS", "white", on_color="on_cyan", attrs=["bold"]))
    print("-"*70)
    time.sleep(0.5)  # Add slight delay for better readability
    
    print("\n🔥 Testing Liquidation Data:")
    liq_df = api.get_liq_data(symbol)
    print("\n")
    time.sleep(0.5)
    
    print("💰 Testing Funding Rate Data:")
    funding_df = api.get_funding_rate(symbol)
    print("\n")
    time.sleep(0.5)
    
    print("📈 Testing Open Interest Data:")
    oi_df = api.get_open_interest(symbol)
    print("\n")
    time.sleep(0.5)
    
    print("📊 Testing Total Open Interest Data:")
    total_oi_df = api.get_open_interest(symbol, total=True)
    print("\n")
    time.sleep(0.5)
    
    print("🆕 Testing New Token Launches:")
    new_tokens_df = api.get_new_token_addresses()
    print("\n")
    time.sleep(0.5)

    # Test copybot endpoints
    print(colored("🤖  COPYBOT ENDPOINTS", "white", on_color="on_green", attrs=["bold"]))
    print("-"*70)
    time.sleep(0.5)
    
    print("\n👥 Testing Follow List:")
    follow_list = api.get_copybot_follow_list()
    print("\n")
    time.sleep(0.5)
    
    print("🔄 Testing Recent Transactions:")
    recent_txs = api.get_recent_transactions()
    print("\n")
    time.sleep(0.5)

    # List all available files
    print(colored("📁  AVAILABLE FILES", "white", on_color="on_magenta", attrs=["bold"]))
    print("-"*70)
    api.list_available_files()
    print("\n")

    print("="*70)
    print(colored("✨  Moon Dev's API Test Complete!  ✨", "white", on_color="on_cyan", attrs=["bold"]))
    print("="*70 + "\n")
