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
    """Run the trading and risk agents in sequence"""
    try:
        trading_agent = TradingAgent() if ACTIVE_AGENTS['trading'] else None
        risk_agent = RiskAgent() if ACTIVE_AGENTS['risk'] else None

        while True:
            # Only run risk checks if risk agent is active
            if risk_agent:
                cprint("\n🛡️ Running Risk Agent...", "cyan")
                risk_agent.log_daily_balance()
                
                # Check if PnL limits are hit
                if risk_agent.check_pnl_limits():
                    limit_type = "percentage" if USE_PERCENTAGE else "USD"
                    cprint(f"\n⚠️ PnL limit hit ({limit_type}-based) - Balance changed from ${risk_agent.start_balance:.2f} to ${risk_agent.current_value:.2f}", "red")
                    cprint("Skipping trading until next check...", "yellow")
                    time.sleep(60 * SLEEP_BETWEEN_RUNS_MINUTES)
                    continue

            # Run trading agent if it's active (and if risk checks pass or risk agent is off)
            if trading_agent:
                cprint("\n🤖 Running Trading Agent...", "cyan")
                trading_agent.run_trading_cycle()

                # Run risk agent again after trading if it's active
                if risk_agent:
                    cprint("\n🛡️ Running Risk Agent Post-Trade...", "cyan")
                    if risk_agent.check_pnl_limits():
                        limit_type = "percentage" if USE_PERCENTAGE else "USD"
                        cprint(f"\n⚠️ PnL limit hit ({limit_type}-based) - Balance changed from ${risk_agent.start_balance:.2f} to ${risk_agent.current_value:.2f}", "red")

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
