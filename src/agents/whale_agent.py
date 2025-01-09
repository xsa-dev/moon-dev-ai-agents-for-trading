"""
🐳 Moon Dev's Whale Watcher
Built with love by Moon Dev 🚀

Dez the Whale Agent tracks open interest changes across different timeframes and announces market moves via OpenAI TTS.
"""

import os
import pandas as pd
import time
from datetime import datetime, timedelta
from termcolor import colored, cprint
from dotenv import load_dotenv
import openai
from pathlib import Path
from src import nice_funcs as n
from src.agents.api import MoonDevAPI
from collections import deque
from src.agents.base_agent import BaseAgent
import traceback
import numpy as np

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
CHECK_INTERVAL_MINUTES = 10  # How often to check OI (can be set to 0.5 for 30 seconds)
LOOKBACK_PERIODS = {
    '15min': 15  # Simplified to just 15 minutes
}

# Voice settings
VOICE_MODEL = "tts-1"  # or tts-1-hd for higher quality
VOICE_NAME = "shimmer"   # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1      # 0.25 to 4.0

class WhaleAgent(BaseAgent):
    """Dez the Whale Watcher 🐋"""
    
    def __init__(self):
        """Initialize Dez the Whale Agent"""
        super().__init__('whale')  # Initialize base agent with type
        
        load_dotenv()
        
        # Get API key using the correct environment variable name
        api_key = os.getenv("OPENAI_KEY")
        if not api_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        openai.api_key = api_key
        
        self.api = MoonDevAPI()
        
        # Create data directories if they don't exist
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load historical data
        self.history_file = self.data_dir / "oi_history.csv"
        self.load_history()
        
        print("🐋 Dez the Whale Agent initialized!")
        
    def load_history(self):
        """Load or initialize historical OI data with change tracking"""
        try:
            if self.history_file.exists():
                df = pd.read_csv(self.history_file)
                
                # Check if we have the new column format
                required_columns = ['timestamp', 'btc_oi', 'eth_oi', 'total_oi', 'btc_change_pct', 'eth_change_pct', 'total_change_pct']
                if all(col in df.columns for col in required_columns):
                    self.oi_history = df
                    self.oi_history['timestamp'] = pd.to_datetime(self.oi_history['timestamp'])
                    print(f"📈 Loaded {len(self.oi_history)} historical OI records")
                else:
                    print("📝 Detected old format, creating new history file")
                    self.oi_history = pd.DataFrame(columns=required_columns)
                    self.history_file.unlink()
            else:
                self.oi_history = pd.DataFrame(columns=['timestamp', 'btc_oi', 'eth_oi', 'total_oi', 
                                                      'btc_change_pct', 'eth_change_pct', 'total_change_pct'])
                print("📝 Created new OI history file")
                
            # Clean up old data (keep only last 24 hours)
            if not self.oi_history.empty:
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.oi_history = self.oi_history[self.oi_history['timestamp'] > cutoff_time]
                self.oi_history.to_csv(self.history_file, index=False)
                
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            self.oi_history = pd.DataFrame(columns=['timestamp', 'btc_oi', 'eth_oi', 'total_oi'])
            
    def _save_oi_data(self, timestamp, btc_oi, eth_oi, total_oi):
        """Save new OI data point with change percentages"""
        try:
            # Calculate percentage changes if we have previous data
            btc_change_pct = eth_change_pct = total_change_pct = 0.0
            
            if not self.oi_history.empty:
                prev_data = self.oi_history.iloc[-1]
                print("\n📊 Previous vs Current OI:")
                print(f"Previous BTC OI: ${prev_data['btc_oi']:,.2f}")
                print(f"Current BTC OI: ${btc_oi:,.2f}")
                
                btc_change_pct = ((btc_oi - prev_data['btc_oi']) / prev_data['btc_oi']) * 100
                eth_change_pct = ((eth_oi - prev_data['eth_oi']) / prev_data['eth_oi']) * 100
                total_change_pct = ((total_oi - prev_data['total_oi']) / prev_data['total_oi']) * 100
                
                print(f"\n📈 Calculated Changes:")
                print(f"BTC Change: {btc_change_pct:.4f}%")
                print(f"ETH Change: {eth_change_pct:.4f}%")
                print(f"Total Change: {total_change_pct:.4f}%")
            
            # Add new data point
            new_row = pd.DataFrame([{
                'timestamp': timestamp,
                'btc_oi': float(btc_oi),
                'eth_oi': float(eth_oi),
                'total_oi': float(total_oi),
                'btc_change_pct': btc_change_pct,
                'eth_change_pct': eth_change_pct,
                'total_change_pct': total_change_pct
            }])
            
            print("\n📝 Adding new data point to history...")
            print(f"History size before: {len(self.oi_history)}")
            self.oi_history = pd.concat([self.oi_history, new_row], ignore_index=True)
            print(f"History size after: {len(self.oi_history)}")
            
            # Clean up old data
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_size = len(self.oi_history)
            self.oi_history = self.oi_history[self.oi_history['timestamp'] > cutoff_time]
            print(f"Removed {old_size - len(self.oi_history)} old records")
            
            # Save to file
            self.oi_history.to_csv(self.history_file, index=False)
            print("💾 Saved to history file")
            
        except Exception as e:
            print(f"❌ Error saving OI data: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            
    def _format_number_for_speech(self, number):
        """Convert numbers to speech-friendly format"""
        billions = number / 1e9
        if billions >= 1:
            return f"{billions:.4f} billion"
        millions = number / 1e6
        return f"{millions:.2f} million"

    def _get_current_oi(self):
        """Get current open interest data"""
        try:
            print("\n🔍 Fetching fresh OI data from API...")
            df = self.api.get_open_interest()
            print(f"📊 Raw OI data shape: {df.shape if df is not None else 'No data received'}")
            
            if df is not None and not df.empty:
                # Get the latest data point
                latest_data = df.iloc[-1]  # Get most recent row
                
                # Extract values directly from our format
                btc_oi = latest_data['btc_oi']
                eth_oi = latest_data['eth_oi']
                total_oi = latest_data['total_oi']
                
                print(f"\n📈 Market OI Breakdown (Fresh from API):")
                print(f"BTC: ${btc_oi:,.2f}")
                print(f"ETH: ${eth_oi:,.2f}")
                print(f"Total: ${total_oi:,.2f}")
                
                timestamp = datetime.now()
                print(f"\n💾 Saving data point at {timestamp}")
                self._save_oi_data(timestamp, btc_oi, eth_oi, total_oi)
                return total_oi
                
            print("❌ No data received from API")
            return None
            
        except Exception as e:
            print(f"❌ Error getting OI data: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            return None
            
    def _get_historical_oi(self, minutes_ago):
        """Get OI data from X minutes ago"""
        try:
            target_time = datetime.now() - timedelta(minutes=minutes_ago)
            
            # Find closest data point before target time
            historical_data = self.oi_history[self.oi_history['timestamp'] <= target_time]
            
            if not historical_data.empty:
                return float(historical_data.iloc[-1]['total_oi'])
            return None
            
        except Exception as e:
            print(f"❌ Error getting historical OI: {str(e)}")
            return None
        
    def _calculate_changes(self, current_oi):
        """Calculate OI changes for the configured interval"""
        changes = {}
        
        print("\n📊 Calculating OI Changes:")
        
        # Get current BTC value
        current_btc = float(self.oi_history.iloc[-1]['btc_oi'])
        print(f"Current BTC OI: ${current_btc:,.2f}")
        
        # Use our local CHECK_INTERVAL_MINUTES constant
        interval = CHECK_INTERVAL_MINUTES
        
        # Get historical data from X minutes ago
        historical_data = self.oi_history[
            self.oi_history['timestamp'] <= (datetime.now() - timedelta(minutes=interval))
        ]
        
        if not historical_data.empty:
            historical_btc = float(historical_data.iloc[-1]['btc_oi'])
            print(f"Historical BTC OI ({interval}m ago): ${historical_btc:,.2f}")
            
            # Calculate percentage change
            btc_pct_change = ((current_btc - historical_btc) / historical_btc) * 100
            print(f"Calculated change: {btc_pct_change:.4f}%")
            
            changes = {
                'btc': btc_pct_change,
                'interval': interval,
                'start_btc': historical_btc,
                'current_btc': current_btc
            }
        else:
            print(f"⚠️ No historical data found from {interval}m ago")
        
        return changes
        
    def _format_announcement(self, changes):
        """Format OI changes into a speech-friendly message with whale detection"""
        if changes:
            btc_change = changes['btc']
            interval = changes['interval']
            
            # Format direction
            btc_direction = "up" if btc_change > 0 else "down"
            
            # Check for whale activity
            is_whale = self._detect_whale_activity(btc_change)
            
            # Build message
            if is_whale:
                message = "🐋 Whale Alert! "
            else:
                message = ""
                
            message += f"BTC OI {btc_direction} {abs(btc_change):.3f}% in {interval}m, "
            message += f"from {self._format_number_for_speech(changes['start_btc'])} "
            message += f"to {self._format_number_for_speech(changes['current_btc'])}"
            
            # Return both message and whale status
            return message, is_whale
        return None, False
        
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            print("\n📊 Checking Open Interest...")
            current_oi = self._get_current_oi()
            
            if current_oi is None:
                print("❌ Failed to get current OI data")
                return
                
            # Calculate and announce changes if we have enough data
            if len(self.oi_history) > 2:  # Need at least 2 data points
                changes = self._calculate_changes(current_oi)
                if changes:
                    announcement, is_whale = self._format_announcement(changes)
                    if announcement:
                        self._announce(announcement, is_whale)
            else:
                print("📝 Building historical data...")
                
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            
    def _announce(self, message, is_whale=False):
        """Announce a message, only use voice for whale alerts"""
        try:
            print(f"\n🗣️ {message}")
            
            # Only use voice for whale alerts
            if not is_whale:
                return
                
            # Generate unique filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            speech_file = self.audio_dir / f"temp_audio_{timestamp}.mp3"
            
            # Generate speech using OpenAI with proper streaming
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                speed=VOICE_SPEED,
                input=message
            )
            
            # Save and play the audio using the new streaming method
            with open(speech_file, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            # Play the audio (platform specific)
            if os.name == 'posix':  # macOS/Linux
                os.system(f"afplay {speech_file}")
            else:  # Windows
                os.system(f"start {speech_file}")
                time.sleep(5)  # Give it time to start playing
            
            # Delete the file after playing
            try:
                speech_file.unlink()  # Delete the temporary audio file
                print("🧹 Cleaned up temporary audio file")
            except Exception as e:
                print(f"⚠️ Couldn't delete audio file: {e}")
                
        except Exception as e:
            print(f"❌ Error in text-to-speech: {str(e)}")

    def _announce_initial_summary(self):
        """Announce the current state of the market based on existing data"""
        try:
            if self.oi_history.empty:
                current_data = self._get_current_oi()
                if current_data is not None:
                    latest_data = self.oi_history.iloc[-1]
                    btc_oi = latest_data['btc_oi']
                    eth_oi = latest_data['eth_oi']
                    total_oi = latest_data['total_oi']
                    
                    message = "🌙 Moon Dev's Whale Watcher starting fresh! I'll compare changes once I have more data. "
                    message += f"Current total open interest is {self._format_number_for_speech(total_oi)} with Bitcoin at "
                    message += f"{(btc_oi/total_oi)*100:.1f}% and Ethereum at {(eth_oi/total_oi)*100:.1f}% of the market."
                    self._announce(message)
                return
                
            # Rest of the method remains unchanged
            current_oi = float(self.oi_history.iloc[-1]['total_oi'])
            changes = {}
            available_periods = []
            
            # Check what historical data we have
            for period_name, minutes in LOOKBACK_PERIODS.items():
                historical_oi = self._get_historical_oi(minutes)
                if historical_oi is not None:
                    pct_change = ((current_oi - historical_oi) / historical_oi) * 100
                    changes[period_name] = pct_change
                    available_periods.append(period_name)
            
            if not changes:
                earliest_data = self.oi_history.iloc[0]
                latest_data = self.oi_history.iloc[-1]
                minutes_diff = (latest_data['timestamp'] - earliest_data['timestamp']).total_seconds() / 60
                pct_change = ((latest_data['total_oi'] - earliest_data['total_oi']) / earliest_data['total_oi']) * 100
                
                message = f"Open Interest has {('increased' if pct_change > 0 else 'decreased')} "
                message += f"by {abs(pct_change):.1f}% over the last {int(minutes_diff)} minutes."
            else:
                message = "Initial market summary: "
                for period in available_periods:
                    change = changes[period]
                    direction = "up" if change > 0 else "down"
                    message += f"OI is {direction} {abs(change):.1f}% over the last {period}. "
            
            self._announce(message)
            
        except Exception as e:
            print(f"❌ Error in initial summary: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")

    def _detect_whale_activity(self, current_change):
        """Detect if current change is significantly above rolling average"""
        try:
            if len(self.oi_history) < 10:  # Need some history for meaningful average
                print("⚠️ Not enough history for whale detection")
                return False
            
            # Get rolling average of absolute changes
            historical_changes = self.oi_history['btc_change_pct'].abs().rolling(window=10).mean().dropna()
            if historical_changes.empty:
                print("⚠️ No historical changes available")
                return False
                
            avg_change = historical_changes.mean()
            threshold = avg_change * 1.25
            
            print(f"\n🔍 Whale Detection Analysis:")
            print(f"Current change: {abs(current_change):.4f}%")
            print(f"Average change: {avg_change:.4f}%")
            print(f"Threshold (125% of avg): {threshold:.4f}%")
            print(f"Is whale? {'Yes! 🐋' if abs(current_change) > threshold else 'No'}")
            
            return abs(current_change) > threshold
            
        except Exception as e:
            print(f"❌ Error detecting whale activity: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    agent = WhaleAgent()
    
    # Run the agent continuously
    print("\n🐋 Moon Dev's Whale Agent starting monitoring cycle...")
    while True:
        try:
            agent.run_monitoring_cycle()
            time.sleep(60 * CHECK_INTERVAL_MINUTES)  # Sleep for the configured interval
        except KeyboardInterrupt:
            print("\n👋 Whale Agent shutting down gracefully...")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {str(e)}")
            print("🔧 Moon Dev suggests checking the logs and trying again!")
            time.sleep(60)  # Sleep for 1 minute on error 