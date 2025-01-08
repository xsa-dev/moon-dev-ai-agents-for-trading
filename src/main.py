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

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import agents
from src.agents.trading_agent import TradingAgent
from src.agents.risk_agent import RiskAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.copybot_agent import CopyBotAgent

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': True,      # Risk management agent
    'trading': False,   # LLM trading agent
    'strategy': False,  # Strategy-based trading agent
    'copybot': False,    # CopyBot agent
    # Add more agents here as we build them:
    # 'sentiment': False,  # Future sentiment analysis agent
    # 'portfolio': False,  # Future portfolio optimization agent
}

def run_agents():
    """Run all active agents in sequence"""
    try:
        # Initialize active agents
        trading_agent = TradingAgent() if ACTIVE_AGENTS['trading'] else None
        risk_agent = RiskAgent() if ACTIVE_AGENTS['risk'] else None
        strategy_agent = StrategyAgent() if ACTIVE_AGENTS['strategy'] else None
        copybot_agent = CopyBotAgent() if ACTIVE_AGENTS['copybot'] else None

        while True:
            # Run Risk Management Checks
            if risk_agent:
                cprint("\n🛡️ Running Risk Management Checks...", "cyan")
                print("\n💰 Checking current portfolio value...")
                portfolio_value = risk_agent.get_portfolio_value()
                print(f"📊 Current Portfolio Value: ${portfolio_value:.2f}")
                print(f"📉 Minimum Balance Limit: ${MINIMUM_BALANCE_USD:.2f}")
                
                # Check risk limits
                print("\n🔍 Checking risk limits...")
                risk_agent.check_risk_limits()
                
                # Log daily balance
                print("\n📝 Checking if we need to log daily balance...")
                risk_agent.log_daily_balance()

            # Run CopyBot Analysis
            if copybot_agent:
                cprint("\n🤖 Running CopyBot Portfolio Analysis...", "cyan")
                copybot_agent.run_analysis_cycle()

            # Sleep until next cycle
            next_run = datetime.now() + timedelta(minutes=SLEEP_BETWEEN_RUNS_MINUTES)
            cprint(f"\n😴 Sleeping until {next_run.strftime('%H:%M:%S')}", "cyan")
            time.sleep(60 * SLEEP_BETWEEN_RUNS_MINUTES)

    except KeyboardInterrupt:
        cprint("\n👋 Gracefully shutting down...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Error in main loop: {str(e)}", "red")
        raise

if __name__ == "__main__":
    cprint("\n🌙 Moon Dev AI Agent Trading System Starting...", "white", "on_blue")
    cprint("\n📊 Active Agents:", "white", "on_blue")
    for agent, active in ACTIVE_AGENTS.items():
        status = "✅ ON" if active else "❌ OFF"
        cprint(f"  • {agent.title()}: {status}", "white", "on_blue")
    print("\n")
    
    run_agents()
