"""
🌙 Moon Dev's AI Trading System
Main entry point for running trading agents
"""

import os
from termcolor import cprint
from dotenv import load_dotenv
import time
from datetime import datetime

# Import agents
from agents.trading_agent import TradingAgent
from agents.risk_agent import RiskAgent

# Load environment variables
load_dotenv()

# Agent Configuration
ACTIVE_AGENTS = {
    'risk': True,      # Risk management agent
    'trading': False,  # Trading agent
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
            
            # Run risk agent first (if active)
            if 'risk' in agents:
                # Log balance at 8 AM
                if current_time.hour == 8 and current_time.minute < 15:
                    cprint("\n⏰ 8 AM - Logging daily starting balance...", "white", "on_blue")
                    agents['risk'].log_daily_balance()
                
                # Always check PnL limits
                limit_hit = agents['risk'].check_pnl_limits()
                if limit_hit:
                    cprint("⚠️ PnL limit hit - skipping other agents this cycle", "white", "on_yellow")
                    time.sleep(300)  # Sleep 5 minutes
                    continue
            
            # Run trading agent (if active and no limits hit)
            if 'trading' in agents:
                cprint("\n🤖 Running Trading Agent...", "white", "on_blue")
                agents['trading'].run_trading_cycle()
            
            # Add more agents here as we build them
            
            cprint("\n✨ Agent Cycle Complete", "white", "on_green")
            time.sleep(300)  # Sleep 5 minutes between cycles
            
    except KeyboardInterrupt:
        cprint("\n👋 Moon Dev AI System shutting down gracefully...", "white", "on_blue")
    except Exception as e:
        cprint(f"\n❌ Error in main loop: {str(e)}", "white", "on_red")
        cprint("🔧 Moon Dev suggests checking the logs and trying again!", "white", "on_blue")

if __name__ == "__main__":
    cprint("\n🌙 Moon Dev AI Trading System Starting...", "white", "on_blue")
    cprint("\n📊 Active Agents:", "white", "on_blue")
    for agent, active in ACTIVE_AGENTS.items():
        status = "✅ ON" if active else "❌ OFF"
        cprint(f"  • {agent.title()}: {status}", "white", "on_blue")
    print("\n")
    
    run_agents()
