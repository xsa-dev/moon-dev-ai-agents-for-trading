"""
🌊 Moon Dev's Liquidation Monitor
Built with love by Moon Dev 🚀

Liz the Liquidation Agent tracks sudden increases in liquidation volume and announces when she sees potential market moves
"""

import os
import pandas as pd
import time
from datetime import datetime, timedelta
from termcolor import colored, cprint
from dotenv import load_dotenv
import openai
import anthropic
from pathlib import Path
from src import nice_funcs as n
from src import nice_funcs_hl as hl
from src.agents.api import MoonDevAPI
from collections import deque
from src.agents.base_agent import BaseAgent
import traceback
import numpy as np

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
CHECK_INTERVAL_MINUTES = 5  # How often to check liquidations
LIQUIDATION_ROWS = 10000   # Number of rows to fetch each time
LIQUIDATION_THRESHOLD = 1.5  # Multiplier for average liquidation to detect significant events

# Select which time window to use for comparisons (options: 15, 60, 240)
# 15 = 15 minutes (most reactive to sudden changes)
# 60 = 1 hour (medium-term changes)
# 240 = 4 hours (longer-term changes)
COMPARISON_WINDOW = 15  # Default to 15 minutes for quick reactions

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 50  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings
VOICE_MODEL = "tts-1"
VOICE_NAME = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1

# AI Analysis Prompt
LIQUIDATION_ANALYSIS_PROMPT = """

You must respond in exactly 3 lines:
Line 1: Only write BUY, SELL, or NOTHING
Line 2: One short reason why
Line 3: Only write "Confidence: X%" where X is 0-100

Analyze market with {pct_change}% increase in liquidations:
Current Total Liquidations: ${current_size:,.2f}
Previous Total Liquidations: ${previous_size:,.2f}
Time Period: Last {LIQUIDATION_ROWS} liquidation events

Large liquidation increases often indicate potential reversals
Extremely large liquidations can signal capitulation which could lead to a bottom or top
Consider market direction and size of liquidations for context

"""

class LiquidationAgent(BaseAgent):
    """Luna the Liquidation Monitor 🌊"""
    
    def __init__(self):
        """Initialize Luna the Liquidation Agent"""
        super().__init__('liquidation')
        
        # Set AI parameters - use config values unless overridden
        self.ai_model = AI_MODEL if AI_MODEL else config.AI_MODEL
        self.ai_temperature = AI_TEMPERATURE if AI_TEMPERATURE > 0 else config.AI_TEMPERATURE
        self.ai_max_tokens = AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else config.AI_MAX_TOKENS
        
        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of config.py defaults")
            if AI_MODEL:
                print(f"  - Model: {AI_MODEL}")
            if AI_TEMPERATURE > 0:
                print(f"  - Temperature: {AI_TEMPERATURE}")
            if AI_MAX_TOKENS > 0:
                print(f"  - Max Tokens: {AI_MAX_TOKENS}")
                
        load_dotenv()
        
        # Get API keys
        openai_key = os.getenv("OPENAI_KEY")
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        if not anthropic_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        openai.api_key = openai_key
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        
        self.api = MoonDevAPI()
        
        # Create data directories if they don't exist
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load historical data
        self.history_file = self.data_dir / "liquidation_history.csv"
        self.load_history()
        
        print("🌊 Luna the Liquidation Agent initialized!")
        print(f"🎯 Alerting on liquidation increases above {(LIQUIDATION_THRESHOLD-1)*100:.0f}%")
        print(f"📊 Analyzing last {LIQUIDATION_ROWS} liquidation events")
        
    def load_history(self):
        """Load or initialize historical liquidation data"""
        try:
            if self.history_file.exists():
                self.liquidation_history = pd.read_csv(self.history_file)
                print(f"📈 Loaded {len(self.liquidation_history)} historical liquidation records")
            else:
                self.liquidation_history = pd.DataFrame(columns=['timestamp', 'total_size'])
                print("📝 Created new liquidation history file")
                
            # Clean up old data (keep only last 24 hours)
            if not self.liquidation_history.empty:
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.liquidation_history = self.liquidation_history[
                    pd.to_datetime(self.liquidation_history['timestamp']) > cutoff_time
                ]
                self.liquidation_history.to_csv(self.history_file, index=False)
                
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            self.liquidation_history = pd.DataFrame(columns=['timestamp', 'total_size'])
            
    def _get_current_liquidations(self):
        """Get current liquidation data"""
        try:
            print("\n🔍 Fetching fresh liquidation data...")
            df = self.api.get_liquidation_data(limit=LIQUIDATION_ROWS)
            
            if df is not None and not df.empty:
                # Set column names
                df.columns = ['symbol', 'side', 'type', 'time_in_force', 
                            'quantity', 'price', 'price2', 'status', 
                            'filled_qty', 'total_qty', 'timestamp', 'usd_value']
                
                # Convert timestamp to datetime (UTC)
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                current_time = datetime.utcnow()
                
                # Calculate time windows
                fifteen_min = current_time - timedelta(minutes=15)
                one_hour = current_time - timedelta(hours=1)
                four_hours = current_time - timedelta(hours=4)
                
                # Calculate totals for each time window
                fifteen_min_total = df[df['datetime'] >= fifteen_min]['usd_value'].sum()
                one_hour_total = df[df['datetime'] >= one_hour]['usd_value'].sum()
                four_hour_total = df[df['datetime'] >= four_hours]['usd_value'].sum()
                
                # Get event counts for each window
                fifteen_min_events = len(df[df['datetime'] >= fifteen_min])
                one_hour_events = len(df[df['datetime'] >= one_hour])
                four_hour_events = len(df[df['datetime'] >= four_hours])
                
                # Calculate percentage change for active window
                pct_change = 0
                if not self.liquidation_history.empty:
                    previous_size = self.liquidation_history['total_size'].iloc[-1]
                    if COMPARISON_WINDOW == 60:
                        current = one_hour_total
                    elif COMPARISON_WINDOW == 240:
                        current = four_hour_total
                    else:
                        current = fifteen_min_total
                    pct_change = ((current - previous_size) / previous_size) * 100 if previous_size > 0 else 0
                
                # Print fun box with liquidation info
                print("\n" + "╔" + "═" * 60 + "╗")
                print("║            🌙 Moon Dev's Liquidation Party 💦             ║")
                print("╠" + "═" * 60 + "╣")
                
                # Format each line based on which window is active
                if COMPARISON_WINDOW == 15:
                    print(f"║  Last 15min: ${fifteen_min_total:,.2f} ({fifteen_min_events} events) [{pct_change:+.1f}%]".ljust(61) + "║")
                    print(f"║  Last 1hr:   ${one_hour_total:,.2f} ({one_hour_events} events)".ljust(61) + "║")
                    print(f"║  Last 4hrs:  ${four_hour_total:,.2f} ({four_hour_events} events)".ljust(61) + "║")
                elif COMPARISON_WINDOW == 60:
                    print(f"║  Last 15min: ${fifteen_min_total:,.2f} ({fifteen_min_events} events)".ljust(61) + "║")
                    print(f"║  Last 1hr:   ${one_hour_total:,.2f} ({one_hour_events} events) [{pct_change:+.1f}%]".ljust(61) + "║")
                    print(f"║  Last 4hrs:  ${four_hour_total:,.2f} ({four_hour_events} events)".ljust(61) + "║")
                else:  # 240 minutes (4 hours)
                    print(f"║  Last 15min: ${fifteen_min_total:,.2f} ({fifteen_min_events} events)".ljust(61) + "║")
                    print(f"║  Last 1hr:   ${one_hour_total:,.2f} ({one_hour_events} events)".ljust(61) + "║")
                    print(f"║  Last 4hrs:  ${four_hour_total:,.2f} ({four_hour_events} events) [{pct_change:+.1f}%]".ljust(61) + "║")
                
                print("╚" + "═" * 60 + "╝")
                
                # Return the total based on selected comparison window
                if COMPARISON_WINDOW == 60:
                    return one_hour_total
                elif COMPARISON_WINDOW == 240:
                    return four_hour_total
                else:  # Default to 15 minutes
                    return fifteen_min_total
            return None
            
        except Exception as e:
            print(f"❌ Error getting liquidation data: {str(e)}")
            traceback.print_exc()
            return None
            
    def _analyze_opportunity(self, current_size, previous_size):
        """Get AI analysis of the liquidation event"""
        try:
            # Calculate percentage change
            pct_change = ((current_size - previous_size) / previous_size) * 100
            
            # Prepare the context
            context = LIQUIDATION_ANALYSIS_PROMPT.format(
                pct_change=f"{pct_change:.2f}",
                current_size=current_size,
                previous_size=previous_size,
                LIQUIDATION_ROWS=LIQUIDATION_ROWS
            )
            
            print(f"\n🤖 Analyzing liquidation spike with AI...")
            
            # Get AI analysis using instance settings
            message = self.client.messages.create(
                model=self.ai_model,
                max_tokens=self.ai_max_tokens,
                temperature=self.ai_temperature,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            # Handle response
            if not message or not message.content:
                print("❌ No response from AI")
                return None
                
            # Extract the actual text from the TextBlock
            content = message.content
            if isinstance(content, list) and len(content) > 0:
                content = content[0].text if hasattr(content[0], 'text') else str(content[0])
            else:
                content = str(content)
            
            # Now split into lines
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            if not lines:
                print("❌ Empty response from AI")
                return None
                
            # First line should be the action
            action = lines[0].strip().upper()
            if action not in ['BUY', 'SELL', 'NOTHING']:
                print(f"⚠️ Invalid action: {action}")
                return None
                
            # Rest is analysis
            analysis = lines[1] if len(lines) > 1 else ""  # Just take the second line for analysis
            
            # Extract confidence from third line
            confidence = 50  # Default confidence
            if len(lines) > 2:
                try:
                    import re
                    matches = re.findall(r'(\d+)%', lines[2])
                    if matches:
                        confidence = int(matches[0])
                except:
                    print("⚠️ Could not parse confidence, using default")
            
            return {
                'action': action,
                'analysis': analysis,
                'confidence': confidence,
                'pct_change': pct_change
            }
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            traceback.print_exc()
            return None
            
    def _format_announcement(self, analysis):
        """Format liquidation analysis into a speech-friendly message"""
        try:
            if analysis:
                message = (
                    f"ayo moon dev seven seven seven! "
                    f"Liquidations up {analysis['pct_change']:.1f}%! "
                    f"AI suggests {analysis['action']} with {analysis['confidence']}% confidence. "
                    f"Analysis: {analysis['analysis'].split()[0]} 🌙"
                )
                return message
            return None
            
        except Exception as e:
            print(f"❌ Error formatting announcement: {str(e)}")
            return None
            
    def _announce(self, message):
        """Announce message using OpenAI TTS"""
        if not message:
            return
            
        try:
            print(f"\n📢 Announcing: {message}")
            
            # Generate speech
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                input=message,
                speed=VOICE_SPEED
            )
            
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.audio_dir / f"liquidation_alert_{timestamp}.mp3"
            
            response.stream_to_file(audio_file)
            
            # Play audio using system command
            os.system(f"afplay {audio_file}")
            
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")
            
    def _save_to_history(self, total_size):
        """Save current liquidation data to history"""
        try:
            if total_size is not None:
                # Create new row
                new_row = pd.DataFrame([{
                    'timestamp': datetime.now(),
                    'total_size': total_size
                }])
                
                # Add to history
                if self.liquidation_history.empty:
                    self.liquidation_history = new_row
                else:
                    self.liquidation_history = pd.concat([self.liquidation_history, new_row], ignore_index=True)
                
                # Keep only last 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.liquidation_history = self.liquidation_history[
                    pd.to_datetime(self.liquidation_history['timestamp']) > cutoff_time
                ]
                
                # Save to file
                self.liquidation_history.to_csv(self.history_file, index=False)
                
        except Exception as e:
            print(f"❌ Error saving to history: {str(e)}")
            traceback.print_exc()
            
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Get current liquidation data
            current_size = self._get_current_liquidations()
            
            if current_size is not None:
                # Get previous size
                if not self.liquidation_history.empty:
                    previous_size = self.liquidation_history['total_size'].iloc[-1]
                    
                    # Check if we have a significant increase
                    if current_size > (previous_size * LIQUIDATION_THRESHOLD):
                        # Get AI analysis
                        analysis = self._analyze_opportunity(current_size, previous_size)
                        
                        if analysis:
                            # Format and announce
                            message = self._format_announcement(analysis)
                            if message:
                                self._announce(message)
                                
                                # Print detailed analysis
                                print("\n" + "╔" + "═" * 50 + "╗")
                                print("║        🌙 Moon Dev's Liquidation Analysis 💦       ║")
                                print("╠" + "═" * 50 + "╣")
                                print(f"║  Action: {analysis['action']:<41} ║")
                                print(f"║  Confidence: {analysis['confidence']}%{' '*36} ║")
                                analysis_lines = analysis['analysis'].split('\n')
                                for line in analysis_lines:
                                    print(f"║  {line:<47} ║")
                                print("╚" + "═" * 50 + "╝")
                
                # Save to history
                self._save_to_history(current_size)
                
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            traceback.print_exc()

    def run(self):
        """Run the liquidation monitor continuously"""
        print("\n🌊 Starting liquidation monitoring...")
        
        while True:
            try:
                self.run_monitoring_cycle()
                print(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Luna the Liquidation Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying

if __name__ == "__main__":
    agent = LiquidationAgent()
    agent.run()
