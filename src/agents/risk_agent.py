'''
I'm building this risk agent to be very easy for a hand trader to use. So alongside of their admittedly 
stupid hand trading, at least they'll have an AI agent to help them out. The thought is, is if we build 
this risk agent out first, it's going to be easy for manual traders to improve them, improve their 
trading by having an AI agent trade along with them. This is also an essential part of any good trader. 
So later we will have a risk agent running with our trading agent. So whether human or AI, this risk agent
running at all times will make the system better. 

risk agent 
- constantly monitoring daily max loss and max gain (closing positions if either are hit)
    - get balance at start of day and log to a csv with pandas 
    - every run, check the balance and make sure that - max loss or + max gain is not hit
    - if hit, send the agent the data of the past 8 hours on the 15m and also the 2 hours 5 min to 
        see if it should overide the max loss or max gain. this should rarely happen, but in the case
        of a big move in our direction, it will give us the ability to keep the position opne a bit longer
        but then every 15 minutes ask the agent again to see if it should abide or keep riding
        i want to weight this more to happen less on the max loss and more on the max gain. 
    
- constantly monitoring entrys to ensure they are only in sz/dz (on some timeframe)
'''

import anthropic
import os
import pandas as pd
import json
from termcolor import colored, cprint
from dotenv import load_dotenv
from .. import config
from .. import nice_funcs as n
from ..data.ohlcv_collector import collect_all_tokens
from datetime import datetime, timedelta
import time

# Load environment variables
load_dotenv()

class RiskAgent:
    def __init__(self):
        """Initialize Moon Dev's Risk Agent 🛡️"""
        api_key = os.getenv("ANTHROPIC_KEY")
        if not api_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        self.client = anthropic.Anthropic(api_key=api_key)
        self.override_active = False
        self.last_override_check = None
        print("🛡️ Moon Dev's Risk Agent initialized!")
        
    def get_portfolio_value(self):
        """Calculate total portfolio value in USD"""
        total_value = 0.0
        
        try:
            # Get USDC balance first
            usdc_value = n.get_token_balance_usd(config.USDC_ADDRESS)
            total_value += usdc_value
            
            # Get balance of each monitored token
            for token in config.MONITORED_TOKENS:
                if token != config.USDC_ADDRESS:  # Skip USDC as we already counted it
                    token_value = n.get_token_balance_usd(token)
                    total_value += token_value
                    
            return total_value
            
        except Exception as e:
            cprint(f"❌ Error calculating portfolio value: {str(e)}", "white", "on_red")
            return 0.0

    def log_daily_balance(self):
        """Log portfolio value at 8:00 AM daily"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('src/data', exist_ok=True)
            
            # Get current portfolio value
            current_value = self.get_portfolio_value()
            
            # Create or load existing balance log
            balance_file = 'src/data/portfolio_balance.csv'
            if os.path.exists(balance_file):
                df = pd.read_csv(balance_file)
            else:
                df = pd.DataFrame(columns=['timestamp', 'balance'])
            
            # Add new row
            new_row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance': current_value
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save updated log
            df.to_csv(balance_file, index=False)
            cprint(f"💾 Portfolio balance logged: ${current_value:.2f}", "white", "on_green")
            
        except Exception as e:
            cprint(f"❌ Error logging daily balance: {str(e)}", "white", "on_red")

    def get_position_data(self, token):
        """Get recent market data for a token"""
        try:
            # Get 8h of 15m data
            data_15m = n.get_data(token, 0.33, '15m')  # 8 hours = 0.33 days
            
            # Get 2h of 5m data
            data_5m = n.get_data(token, 0.083, '5m')   # 2 hours = 0.083 days
            
            return {
                '15m': data_15m.to_dict() if data_15m is not None else None,
                '5m': data_5m.to_dict() if data_5m is not None else None
            }
        except Exception as e:
            cprint(f"❌ Error getting data for {token}: {str(e)}", "white", "on_red")
            return None

    def should_override_limit(self, limit_type):
        """Ask AI if we should override the limit based on recent market data"""
        try:
            # Only check every 15 minutes
            if (self.last_override_check and 
                datetime.now() - self.last_override_check < timedelta(minutes=15)):
                return self.override_active
            
            # Collect data for all active positions
            position_data = {}
            for token in config.MONITORED_TOKENS:
                if token != config.USDC_ADDRESS:
                    current_value = n.get_token_balance_usd(token)
                    if current_value > 0:  # Only get data for active positions
                        cprint(f"📊 Getting market data for {token}...", "white", "on_blue")
                        token_data = self.get_position_data(token)
                        if token_data:
                            position_data[token] = {
                                'value_usd': current_value,
                                'data': token_data
                            }
            
            if not position_data:
                cprint("❌ No active positions found", "white", "on_red")
                return False
                
            # Format data for AI analysis
            prompt = f"""
            You are Moon Dev's Risk Management AI 🛡️
            
            We've hit a {limit_type} limit and need to decide whether to override it.
            
            Analyze the provided market data for each position and decide if we should override the daily limit.
            Consider for each position:
            1. Recent price action and momentum (both 15m and 5m timeframes)
            2. Volume patterns and trends
            3. Market conditions and volatility
            4. Risk/reward ratio based on current position size
            
            Current Positions:
            {json.dumps(position_data, indent=2)}
            
            For max loss overrides:
            - Be EXTREMELY conservative
            - Only override if strong reversal signals
            - Require 90%+ confidence
            - All positions must show reversal potential
            
            For max gain overrides:
            - Can be more lenient
            - Look for continued momentum
            - Require 60%+ confidence
            - Most positions should show upward momentum
            
            Respond with either:
            OVERRIDE: <detailed reason for each position>
            or
            RESPECT_LIMIT: <detailed reason for each position>
            """
            
            cprint("🤖 AI Agent analyzing market data...", "white", "on_blue")
            message = self.client.messages.create(
                model=config.AI_MODEL,
                max_tokens=config.AI_MAX_TOKENS,
                temperature=config.AI_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response = message.content
            self.last_override_check = datetime.now()
            self.override_active = response.startswith("OVERRIDE")
            
            # Print the AI's reasoning
            cprint("\n🧠 AI Agent's Analysis:", "white", "on_blue")
            print(response)
            
            return self.override_active
            
        except Exception as e:
            cprint(f"❌ Error in override check: {str(e)}", "white", "on_red")
            return False

    def check_pnl_limits(self):
        """Check if portfolio value exceeds max loss/gain limits"""
        try:
            balance_file = 'src/data/portfolio_balance.csv'
            if not os.path.exists(balance_file):
                cprint("⚠️ No balance history found", "white", "on_yellow")
                return
                
            # Load balance history
            df = pd.read_csv(balance_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Get today's starting balance (8 AM)
            today_8am = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            if datetime.now().hour < 8:
                today_8am -= timedelta(days=1)
                
            start_balance = df[df['timestamp'] <= today_8am].iloc[-1]['balance']
            current_value = self.get_portfolio_value()
            
            # Calculate limits
            max_loss_limit = start_balance - config.DAILY_MAX_LOSS
            max_gain_limit = start_balance + config.DAILY_MAX_GAIN
            
            cprint(f"\n📊 Portfolio PnL Check", "white", "on_blue")
            cprint(f"🌅 Start Balance: ${start_balance:.2f}", "white", "on_blue")
            cprint(f"📈 Current Value: ${current_value:.2f}", "white", "on_blue")
            cprint(f"⚠️ Loss Limit: ${max_loss_limit:.2f}", "white", "on_blue")
            cprint(f"🎯 Gain Limit: ${max_gain_limit:.2f}", "white", "on_blue")
            
            # Check if we need to close positions
            if current_value <= max_loss_limit:
                cprint(f"🚨 Max daily loss limit reached!", "white", "on_red")
                if self.should_override_limit("loss"):
                    cprint("🤖 AI Agent suggests keeping positions open", "white", "on_yellow")
                    return False
                else:
                    cprint("🛡️ AI Agent confirms - closing all positions", "white", "on_red")
                    self.close_all_positions()
                    return True
                    
            elif current_value >= max_gain_limit:
                cprint(f"🎉 Max daily gain limit reached!", "white", "on_green")
                if self.should_override_limit("gain"):
                    cprint("🤖 AI Agent suggests keeping positions open", "white", "on_yellow")
                    return False
                else:
                    cprint("🛡️ AI Agent confirms - closing all positions", "white", "on_green")
                    self.close_all_positions()
                    return True
                    
            return False
            
        except Exception as e:
            cprint(f"❌ Error checking PnL limits: {str(e)}", "white", "on_red")
            return False

    def close_all_positions(self):
        """Close all open positions using chunk_kill"""
        try:
            for token in config.MONITORED_TOKENS:
                if token != config.USDC_ADDRESS:  # Skip USDC
                    current_value = n.get_token_balance_usd(token)
                    if current_value > 0:
                        cprint(f"\n📉 Closing position for {token}", "white", "on_cyan")
                        n.chunk_kill(token, config.max_usd_order_size, config.slippage)
                        
            cprint("✨ All positions closed!", "white", "on_green")
            
        except Exception as e:
            cprint(f"❌ Error closing positions: {str(e)}", "white", "on_red")

def main():
    """Main function to run the risk agent"""
    cprint("🛡️ Moon Dev's Risk Agent Starting...", "white", "on_blue")
    
    agent = RiskAgent()
    
    while True:
        try:
            current_time = datetime.now()
            
            # Log balance at 8 AM
            if current_time.hour == 8 and current_time.minute < 15:  # Between 8:00-8:15 AM
                cprint("\n⏰ 8 AM - Logging daily starting balance...", "white", "on_blue")
                agent.log_daily_balance()
            
            # Always check PnL limits
            agent.check_pnl_limits()
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
                
        except KeyboardInterrupt:
            print("\n👋 Moon Dev Risk Agent shutting down gracefully...")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("🔧 Moon Dev suggests checking the logs and trying again!")
            time.sleep(300)  # Still sleep on error

if __name__ == "__main__":
    main()

