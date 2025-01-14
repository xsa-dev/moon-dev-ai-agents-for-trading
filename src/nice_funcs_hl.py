'''
nice functions from hyper liquid i can use

🌙 Moon Dev's Hyperliquid Functions
Built with love by Moon Dev 🚀
'''

import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
import time
import pandas_ta as ta  # For technical indicators
import traceback

# Constants
BATCH_SIZE = 5000  # MAX IS 5000 FOR HYPERLIQUID
MAX_RETRIES = 3
MAX_ROWS = 5000
BASE_URL = 'https://api.hyperliquid.xyz/info'

# Global variable to store timestamp offset
timestamp_offset = None

def adjust_timestamp(dt):
    """Adjust API timestamps by subtracting the timestamp offset."""
    if timestamp_offset is not None:
        corrected_dt = dt - timestamp_offset
        return corrected_dt
    return dt

def _get_ohlcv(symbol, interval, start_time, end_time, batch_size=BATCH_SIZE):
    """Internal function to fetch OHLCV data from Hyperliquid"""
    global timestamp_offset
    print(f'\n🔍 Requesting data for {symbol}:')
    print(f'📊 Batch Size: {batch_size}')
    print(f'🚀 Start: {start_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print(f'🎯 End: {end_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')

    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                BASE_URL,
                headers={'Content-Type': 'application/json'},
                json={
                    "type": "candleSnapshot",
                    "req": {
                        "coin": symbol,
                        "interval": interval,
                        "startTime": start_ts,
                        "endTime": end_ts,
                        "limit": batch_size
                    }
                },
                timeout=10
            )

            if response.status_code == 200:
                snapshot_data = response.json()
                if snapshot_data:
                    # Handle timestamp offset
                    if timestamp_offset is None:
                        latest_api_timestamp = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                        system_current_date = datetime.utcnow()
                        expected_latest_timestamp = system_current_date
                        timestamp_offset = latest_api_timestamp - expected_latest_timestamp
                        print(f"⏱️ Calculated timestamp offset: {timestamp_offset}")

                    # Adjust timestamps
                    for candle in snapshot_data:
                        dt = datetime.utcfromtimestamp(candle['t'] / 1000)
                        adjusted_dt = adjust_timestamp(dt)
                        candle['t'] = int(adjusted_dt.timestamp() * 1000)

                    first_time = datetime.utcfromtimestamp(snapshot_data[0]['t'] / 1000)
                    last_time = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                    print(f'✨ Received {len(snapshot_data)} candles')
                    print(f'📈 First: {first_time}')
                    print(f'📉 Last: {last_time}')
                    return snapshot_data
                print('❌ No data returned by API')
                return None
            print(f'⚠️ HTTP Error {response.status_code}: {response.text}')
        except requests.exceptions.RequestException as e:
            print(f'⚠️ Request failed (attempt {attempt + 1}): {e}')
            time.sleep(1)
    return None

def _process_data_to_df(snapshot_data):
    """Convert raw API data to DataFrame"""
    if snapshot_data:
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        data = []
        for snapshot in snapshot_data:
            timestamp = datetime.utcfromtimestamp(snapshot['t'] / 1000)
            # Convert all numeric values to float
            data.append([
                timestamp,
                float(snapshot['o']),
                float(snapshot['h']),
                float(snapshot['l']),
                float(snapshot['c']),
                float(snapshot['v'])
            ])
        df = pd.DataFrame(data, columns=columns)
        
        # Ensure numeric columns are float64
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype('float64')
        
        print("\n📊 OHLCV Data Types:")
        print(df.dtypes)
        
        return df
    return pd.DataFrame()

def add_technical_indicators(df):
    """Add technical indicators to the dataframe"""
    if df.empty:
        return df
        
    try:
        print("\n🔧 Adding technical indicators...")
        
        # Ensure numeric columns are float64
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype('float64')
        
        # Add basic indicators
        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # Add MACD
        macd = ta.macd(df['close'])
        df = pd.concat([df, macd], axis=1)
        
        # Add Bollinger Bands
        bbands = ta.bbands(df['close'])
        df = pd.concat([df, bbands], axis=1)
        
        print("✅ Technical indicators added successfully")
        return df
        
    except Exception as e:
        print(f"❌ Error adding technical indicators: {str(e)}")
        traceback.print_exc()
        return df

def get_data(symbol, timeframe='15m', bars=100, add_indicators=True):
    """
    🌙 Moon Dev's Hyperliquid Data Fetcher
    
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC', 'ETH')
        timeframe (str): Candle timeframe (default: '15m')
        bars (int): Number of bars to fetch (default: 100, max: 5000)
        add_indicators (bool): Whether to add technical indicators
    
    Returns:
        pd.DataFrame: OHLCV data with columns [timestamp, open, high, low, close, volume]
                     and technical indicators if requested
    """
    print("\n🌙 Moon Dev's Hyperliquid Data Fetcher")
    print(f"🎯 Symbol: {symbol}")
    print(f"⏰ Timeframe: {timeframe}")
    print(f"📊 Requested bars: {min(bars, MAX_ROWS)}")

    # Ensure we don't exceed max rows
    bars = min(bars, MAX_ROWS)
    
    # Calculate time window
    end_time = datetime.utcnow()
    # Add extra time to ensure we get enough bars
    start_time = end_time - timedelta(days=60)

    data = _get_ohlcv(symbol, timeframe, start_time, end_time, batch_size=bars)
    
    if not data:
        print("❌ No data available.")
        return pd.DataFrame()

    df = _process_data_to_df(data)

    if not df.empty:
        # Get the most recent bars
        df = df.sort_values('timestamp', ascending=False).head(bars).sort_values('timestamp')
        df = df.reset_index(drop=True)
        
        # Add technical indicators if requested
        if add_indicators:
            df = add_technical_indicators(df)

        print("\n📊 Data summary:")
        print(f"📈 Total candles: {len(df)}")
        print(f"📅 Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print("✨ Thanks for using Moon Dev's Data Fetcher! ✨")

    return df

def get_market_info():
    """Get current market info for all coins on Hyperliquid"""
    try:
        response = requests.post(
            BASE_URL,
            headers={'Content-Type': 'application/json'},
            json={"type": "allMids"}
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error getting market info: {str(e)}")
        return None 