"""
🐳 Moon Dev's Whale Watcher
Built with love by Moon Dev 🚀

Dave the Whale Agent tracks open interest changes across different timeframes and announces market moves via OpenAI TTS.
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

# Configuration
CHECK_INTERVAL_MINUTES = 1  # How often to check OI (can be set to 0.5 for 30 seconds)
LOOKBACK_PERIODS = {
    '5min': 5,
    '1hour': 60,
    '4hours': 240,
    '24hours': 1440
}

# Voice settings
VOICE_MODEL = "tts-1"  # or tts-1-hd for higher quality
VOICE_NAME = "alloy"   # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1.0      # 0.25 to 4.0

class WhaleAgent(BaseAgent):
    """Dave the Whale Watcher 🐋"""
    
    def __init__(self):
        """Initialize Dave the Whale Agent"""
        super().__init__('whale')  # Initialize base agent with type
        
        load_dotenv()
        
        # Get API key using the correct environment variable name
        api_key = os.getenv("OPENAI_KEY")
        if not api_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        openai.api_key = api_key
        
        self.api = MoonDevAPI()
        
        # Create data directories if they don't exist
        self.audio_dir = Path("src/audio")
        self.data_dir = Path("src/data")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load historical data
        self.history_file = self.data_dir / "oi_history.csv"
        self.load_history()
        
        print("🐋 Dave the Whale Agent initialized!")
        self._announce("Dave the Whale Agent is now watching the markets!")
        
    def load_history(self):
        """Load or initialize historical OI data"""
        try:
            if self.history_file.exists():
                self.oi_history = pd.read_csv(self.history_file)
                self.oi_history['timestamp'] = pd.to_datetime(self.oi_history['timestamp'])
                print(f"📈 Loaded {len(self.oi_history)} historical OI records")
            else:
                self.oi_history = pd.DataFrame(columns=['timestamp', 'oi'])
                print("📝 Created new OI history file")
                
            # Clean up old data (keep only last 24 hours)
            if not self.oi_history.empty:
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.oi_history = self.oi_history[self.oi_history['timestamp'] > cutoff_time]
                self.oi_history.to_csv(self.history_file, index=False)
                
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            self.oi_history = pd.DataFrame(columns=['timestamp', 'oi'])
            
    def _save_oi_data(self, timestamp, oi_value):
        """Save new OI data point to CSV"""
        try:
            # Add new data point
            new_row = pd.DataFrame([{
                'timestamp': timestamp,
                'oi': oi_value
            }])
            
            self.oi_history = pd.concat([self.oi_history, new_row], ignore_index=True)
            
            # Clean up old data
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.oi_history = self.oi_history[self.oi_history['timestamp'] > cutoff_time]
            
            # Save to file
            self.oi_history.to_csv(self.history_file, index=False)
            
        except Exception as e:
            print(f"❌ Error saving OI data: {str(e)}")
            
    def _get_current_oi(self):
        """Get current open interest data"""
        try:
            oi_data = self.api.get_open_interest()
            if oi_data is not None:
                timestamp = datetime.now()
                self._save_oi_data(timestamp, oi_data)
                return oi_data
            return None
        except Exception as e:
            print(f"❌ Error getting OI data: {str(e)}")
            return None
            
    def _get_historical_oi(self, minutes_ago):
        """Get OI data from X minutes ago"""
        try:
            target_time = datetime.now() - timedelta(minutes=minutes_ago)
            
            # Find closest data point before target time
            historical_data = self.oi_history[self.oi_history['timestamp'] <= target_time]
            
            if not historical_data.empty:
                return historical_data.iloc[-1]['oi']
            return None
            
        except Exception as e:
            print(f"❌ Error getting historical OI: {str(e)}")
            return None
        
    def _calculate_changes(self, current_oi):
        """Calculate OI changes across different timeframes"""
        changes = {}
        
        for period_name, minutes in LOOKBACK_PERIODS.items():
            historical_oi = self._get_historical_oi(minutes)
            if historical_oi is not None:
                pct_change = ((current_oi - historical_oi) / historical_oi) * 100
                changes[period_name] = pct_change
                
        return changes
        
    def _format_announcement(self, changes):
        """Format OI changes into a speech-friendly message"""
        message = "Moon Dev Open Interest Update: "
        
        for period, change in changes.items():
            direction = "increased" if change > 0 else "decreased"
            message += f"In the last {period}, open interest has {direction} by {abs(change):.1f}%. "
            
        return message
        
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            print("\n📊 Checking Open Interest...")
            current_oi = self._get_current_oi()
            
            if current_oi is None:
                print("❌ Failed to get current OI data")
                return
                
            # Only announce changes if we have enough historical data
            if len(self.oi_history) > 5:  # Need at least 5 minutes of data
                changes = self._calculate_changes(current_oi)
                
                if changes:
                    announcement = self._format_announcement(changes)
                    self._announce(announcement)
                    
            else:
                print("📝 Building historical data...")
                
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            
    def run(self):
        """Main loop for the Open Interest Monitor"""
        print(f"\n🔄 Starting OI monitoring every {CHECK_INTERVAL_MINUTES} minutes...")
        
        while True:
            try:
                self.run_monitoring_cycle()
                
                # Sleep until next check
                sleep_time = CHECK_INTERVAL_MINUTES * 60
                next_check = datetime.now() + timedelta(minutes=CHECK_INTERVAL_MINUTES)
                print(f"\n😴 Next check at {next_check.strftime('%H:%M:%S')}")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\n👋 Gracefully shutting down Open Interest Monitor...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute on error

    def _announce(self, message):
        """Announce a message via OpenAI TTS and print"""
        try:
            print(f"\n🗣️ {message}")
            
            # Generate unique filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            speech_file = self.audio_dir / f"oi_update_{timestamp}.mp3"
            
            # Generate speech using OpenAI
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                speed=VOICE_SPEED,
                input=message
            )
            
            # Save and play the audio
            response.stream_to_file(speech_file)
            
            # Play the audio (platform specific)
            if os.name == 'posix':  # macOS/Linux
                os.system(f"afplay {speech_file}")
            else:  # Windows
                os.system(f"start {speech_file}")
                
        except Exception as e:
            print(f"❌ Error in text-to-speech: {str(e)}")

if __name__ == "__main__":
    agent = WhaleAgent()
    agent.run() 