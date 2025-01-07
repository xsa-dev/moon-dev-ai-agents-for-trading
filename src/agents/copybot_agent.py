"""
🌙 Moon Dev's CopyBot Agent
Analyzes current copybot positions to identify opportunities for increased position sizes
"""

import os
import pandas as pd
import anthropic
from termcolor import colored, cprint
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
from src.config import *
from src import nice_funcs as n
from src.data.ohlcv_collector import collect_all_tokens

# Data path for current copybot portfolio
COPYBOT_PORTFOLIO_PATH = '/Users/md/Dropbox/dev/github/solana-copy-trader/csvs/current_portfolio.csv'

# LLM Prompts
PORTFOLIO_ANALYSIS_PROMPT = """
You are Moon Dev's CopyBot Agent 🌙

Your task is to analyze the current copybot portfolio positions and market data to identify which positions deserve larger allocations.

Data provided:
1. Current copybot portfolio positions and their performance
2. OHLCV market data for each position
3. Technical indicators (MA20, MA40, RSI)

Analysis Criteria:
1. Position performance metrics
2. Price action and momentum
3. Volume analysis
4. Risk/reward ratio
5. Market conditions

{portfolio_data}
{market_data}

Respond in this exact format:
1. First line must be one of: BUY, SELL, or NOTHING (in caps)
2. Then explain your reasoning, including:
   - Position analysis
   - Technical analysis
   - Volume profile
   - Risk assessment
   - Market conditions
   - Confidence level (as a percentage, e.g. 75%)

Remember: 
- Moon Dev always prioritizes risk management! 🛡️
- Never trade USDC or SOL directly
- Look for high-conviction setups
- Consider both position performance and market conditions
- Larger positions need stronger confirmation signals
"""

class CopyBotAgent:
    """Moon Dev's CopyBot Agent 🤖"""
    
    def __init__(self):
        """Initialize the CopyBot agent with LLM"""
        load_dotenv()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
        self.recommendations_df = pd.DataFrame(columns=['token', 'action', 'confidence', 'reasoning'])
        print("🤖 Moon Dev's CopyBot Agent initialized!")
        
    def load_portfolio_data(self):
        """Load current copybot portfolio data"""
        try:
            if not os.path.exists(COPYBOT_PORTFOLIO_PATH):
                print(f"❌ Portfolio file not found: {COPYBOT_PORTFOLIO_PATH}")
                return False
                
            self.portfolio_df = pd.read_csv(COPYBOT_PORTFOLIO_PATH)
            print("💼 Current copybot portfolio loaded!")
            print(self.portfolio_df)
            return True
        except Exception as e:
            print(f"❌ Error loading portfolio data: {str(e)}")
            return False
            
    def analyze_position(self, token):
        """Analyze a single portfolio position"""
        try:
            if token in EXCLUDED_TOKENS:
                print(f"⚠️ Skipping analysis for excluded token: {token}")
                return None
                
            # Get position data
            position_data = self.portfolio_df[self.portfolio_df['Mint Address'] == token]
            if position_data.empty:
                print(f"⚠️ No portfolio data for token: {token}")
                return None
                
            print(f"\n🔍 Analyzing position for {position_data['name'].values[0]}...")
            print(f"💰 Current Amount: {position_data['Amount'].values[0]}")
            print(f"💵 USD Value: ${position_data['USD Value'].values[0]:.2f}")
                
            # Get OHLCV data
            market_data = collect_all_tokens()
            token_market_data = market_data.get(token, "No market data available")
            
            # Prepare context for LLM
            analysis_context = f"""
Portfolio Position:
{position_data.to_string()}

Market Data:
{token_market_data}
"""
            print("\n🤖 Sending data to Moon Dev's AI for analysis...")
            
            # Get LLM analysis
            message = self.client.messages.create(
                model=AI_MODEL,
                max_tokens=AI_MAX_TOKENS,
                temperature=AI_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": f"{PORTFOLIO_ANALYSIS_PROMPT.format(portfolio_data=position_data.to_string(), market_data=token_market_data)}"
                }]
            )
            
            # Parse response
            response = message.content
            if isinstance(response, list):
                response = '\n'.join([
                    item.text if hasattr(item, 'text') else str(item)
                    for item in response
                ])
            
            print("\n🎯 AI Analysis Results:")
            print("=" * 50)
            print(response)
            print("=" * 50)
            
            lines = response.split('\n')
            action = lines[0].strip() if lines else "NOTHING"
            
            # Extract confidence
            confidence = 0
            for line in lines:
                if 'confidence' in line.lower():
                    try:
                        confidence = int(''.join(filter(str.isdigit, line)))
                    except:
                        confidence = 50
            
            # Store recommendation
            reasoning = '\n'.join(lines[1:]) if len(lines) > 1 else "No detailed reasoning provided"
            self.recommendations_df = pd.concat([
                self.recommendations_df,
                pd.DataFrame([{
                    'token': token,
                    'action': action,
                    'confidence': confidence,
                    'reasoning': reasoning
                }])
            ], ignore_index=True)
            
            print(f"\n📊 Summary for {position_data['name'].values[0]}:")
            print(f"Action: {action}")
            print(f"Confidence: {confidence}%")
            print(f"🎯 Position Analysis Complete!")
            return response
            
        except Exception as e:
            print(f"❌ Error analyzing position: {str(e)}")
            return None
            
    def execute_position_updates(self):
        """Execute position size updates based on analysis"""
        try:
            print("\n🚀 Moon Dev executing position updates...")
            
            for _, row in self.recommendations_df.iterrows():
                token = row['token']
                action = row['action']
                confidence = row['confidence']
                
                if action == "NOTHING" or token in EXCLUDED_TOKENS:
                    continue
                    
                if confidence < STRATEGY_MIN_CONFIDENCE:
                    print(f"⚠️ Skipping {token}: Confidence {confidence}% below threshold")
                    continue
                
                print(f"\n🎯 Processing {action} for {token}...")
                # Add your position sizing logic here
                
        except Exception as e:
            print(f"❌ Error updating positions: {str(e)}")
            
    def run_analysis_cycle(self):
        """Run a complete portfolio analysis cycle"""
        try:
            print("\n🌙 Starting Moon Dev CopyBot Portfolio Analysis...")
            
            # Load portfolio data
            if not self.load_portfolio_data():
                return
                
            # Get unique tokens from portfolio
            portfolio_tokens = self.portfolio_df['Mint Address'].unique()
            
            # Analyze each position
            for token in portfolio_tokens:
                self.analyze_position(token)
                
            # Execute position updates
            self.execute_position_updates()
            
            print("\n✨ Portfolio analysis cycle complete!")
            
        except Exception as e:
            print(f"❌ Error in analysis cycle: {str(e)}")

if __name__ == "__main__":
    analyzer = CopyBotAgent()
    analyzer.run_analysis_cycle()