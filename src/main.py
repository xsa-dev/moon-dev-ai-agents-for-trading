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

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': True,      # Risk management agent
    'trading': True,   # LLM trading agent
    'strategy': False,  # Strategy-based trading agent
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

        while True:
            # 1. Run risk checks first
            if risk_agent:
                cprint("\n🛡️ Running Risk Agent...", "cyan")
                risk_agent.log_daily_balance()
                
                if risk_agent.check_pnl_limits():
                    limit_type = "percentage" if USE_PERCENTAGE else "USD"
                    if not risk_agent.should_override_limit(limit_type):
                        cprint(f"\n⚠️ {'PERCENTAGE' if USE_PERCENTAGE else 'USD'} PnL LIMIT REACHED - CLOSING POSITIONS", "white", "on_red")
                        cprint(f"💰 Initial Balance: ${risk_agent.start_balance:.2f}", "yellow")
                        cprint(f"📊 Current Balance: ${risk_agent.current_value:.2f}", "yellow")
                        
                        # Close positions before pausing
                        risk_agent.close_all_positions()
                        
                        cprint(f"⏳ Trading paused for {SLEEP_BETWEEN_RUNS_MINUTES} minutes", "yellow")
                        time.sleep(60 * SLEEP_BETWEEN_RUNS_MINUTES)
                        continue
                    else:
                        cprint("\n🤖 LLM suggests keeping positions open despite PnL limit", "white", "on_yellow")

            # 2. Get strategy signals if enabled
            strategy_signals = None
            if strategy_agent and ENABLE_STRATEGIES:
                cprint("\n🎯 Running Strategy Agent...", "cyan")
                strategy_signals = {}
                for token in MONITORED_TOKENS:
                    signals = strategy_agent.get_signals(token)
                    if signals:
                        strategy_signals[token] = signals

            # 3. Run trading agent with strategy signals
            if trading_agent:
                cprint("\n🤖 Running Trading Agent...", "cyan")
                trading_agent.run_trading_cycle(strategy_signals)

            # 4. Final risk check - I set this to run twice on purpose. Managing isk is everything. 
            if risk_agent:
                cprint("\n🛡️ Running Risk Agent Post-Trade...", "cyan")
                risk_agent.check_pnl_limits()

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
