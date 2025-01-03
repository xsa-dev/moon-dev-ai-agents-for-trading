"""
🌙 Moon Dev's AI Trading System
Main entry point for running trading agents
"""

import os
import sys
from termcolor import cprint
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
from config import *

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents
from src.agents.trading_agent import TradingAgent
from src.agents.risk_agent import RiskAgent

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': True,      # Risk management agent
    'trading': True,  # Trading agent
    # Add more agents here as we build them:
    # 'sentiment': False,  # Future sentiment analysis agent
    # 'portfolio': False,  # Future portfolio optimization agent
}

def run_agents():
    """Initialize and run all active agents"""
    agents = {}
    
    try:
        # Initialize active agents
        if ACTIVE_AGENTS.get('risk'):
            cprint("🛡️ Initializing Risk Agent...", "white", "on_blue")
            agents['risk'] = RiskAgent()
            
        if ACTIVE_AGENTS.get('trading'):
            cprint("🤖 Initializing Trading Agent...", "white", "on_blue")
            agents['trading'] = TradingAgent()
        
        # Main loop
        while True:
            current_time = datetime.now()
            cprint(f"\n⏰ Agent Run Starting at {current_time.strftime('%Y-%m-%d %H:%M:%S')}", "white", "on_green")
            
            # First Risk Check
            if 'risk' in agents:
                cprint("\n🛡️ Running Initial Risk Check...", "white", "on_blue")
                # Log balance at 8 AM
                if current_time.hour == 8 and current_time.minute < 15:
                    cprint("\n⏰ 8 AM - Logging daily starting balance...", "white", "on_blue")
                    agents['risk'].log_daily_balance()
                
                # Check PnL limits
                limit_hit = agents['risk'].check_pnl_limits()
                if limit_hit:
                    cprint("⚠️ PnL limit hit - Balance changed from ${:.2f} to ${:.2f} - skipping trading until next check".format(
                        agents['risk'].start_balance,
                        agents['risk'].current_value
                    ), "white", "on_yellow")
                    time.sleep(5)  # Sleep 5 minutes
                    continue
            
            # Run trading agent if no limits hit
            if 'trading' in agents:
                cprint("\n🤖 Running Trading Agent...", "white", "on_blue")
                agents['trading'].run_trading_cycle()
                
                # Second Risk Check after trading
                if 'risk' in agents:
                    cprint("\n🛡️ Running Post-Trade Risk Check...", "white", "on_blue")
                    limit_hit = agents['risk'].check_pnl_limits()
                    if limit_hit:
                        cprint("⚠️ PnL limit hit after trading - monitoring closely", "white", "on_yellow")
            
            # Add more agents here as we build them
            
            next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
            cprint(f"\n⏳ Agent Cycle Complete. Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}", "white", "on_green")
            time.sleep(SLEEP_BETWEEN_RUNS_MINUTES * 60)  # Convert minutes to seconds
            
    except KeyboardInterrupt:
        cprint("\n👋 Moon Dev AI Agent System shutting down gracefully...", "white", "on_blue")
    except Exception as e:
        cprint(f"\n❌ Error in main loop: {str(e)}", "white", "on_red")
        cprint("🔧 Moon Dev suggests checking the logs and trying again!", "white", "on_blue")

if __name__ == "__main__":
    cprint("\n🌙 Moon Dev AI Agent Trading System Starting...", "white", "on_blue")
    cprint("\n📊 Active Agents:", "white", "on_blue")
    for agent, active in ACTIVE_AGENTS.items():
        status = "✅ ON" if active else "❌ OFF"
        cprint(f"  • {agent.title()}: {status}", "white", "on_blue")
    print("\n")
    
    run_agents()
