"""
🌙 Moon Dev's Base Agent Class
Built with love by Moon Dev 🚀
"""

import os
import time
from datetime import datetime, timedelta
from termcolor import cprint
from src.config import AGENT_INTERVALS

class BaseAgent:
    """Base class for all Moon Dev agents"""
    
    def __init__(self, agent_type):
        """Initialize base agent with type"""
        self.agent_type = agent_type
        self.interval = AGENT_INTERVALS.get(agent_type, 15)  # Default to 15 minutes
        
    def run_standalone(self):
        """Run agent in standalone mode"""
        print(f"\n🚀 Starting {self.agent_type} agent in standalone mode...")
        print(f"⏰ Running every {self.interval} minutes")
        
        while True:
            try:
                self.run_monitoring_cycle()
                
                # Sleep until next check
                next_check = datetime.now() + timedelta(minutes=self.interval)
                print(f"\n😴 Next check at {next_check.strftime('%H:%M:%S')}")
                time.sleep(60 * self.interval)
                
            except KeyboardInterrupt:
                print(f"\n👋 Gracefully shutting down {self.agent_type} agent...")
                break
            except Exception as e:
                print(f"❌ Error in {self.agent_type} agent: {str(e)}")
                time.sleep(60)  # Sleep for a minute on error
                
    def run_monitoring_cycle(self):
        """Override this method in each agent"""
        raise NotImplementedError("Each agent must implement run_monitoring_cycle()") 