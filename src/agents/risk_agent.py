'''
I'm building this risk agent to be very easy for a hand trader to use. So alongside of their admittedly 
stupid hand trading, at least they'll have an AI agent to help them out. The thought is, is if we build 
this risk agent out first, it's going to be easy for manual traders to improve them, improve their 
trading by having an AI agent trade along with them. This is also an essential part of any good trader. 
So later we will have a risk agent running with our trading agent. So whether human or AI, this risk agent
running at all times will make the system better. 

risk agent 
- constantly monitoring daily max loss and max gain (closing positions if either are hit)
- constantly monitoring entrys to ensure they are only in sz/dz (on some timeframe)

'''

import anthropic
import os
import pandas as pd
import json
from termcolor import colored, cprint
from dotenv import load_dotenv
from ..core.config import *
from ..core import nice_funcs as n  # Import nice_funcs as n
from ..data.ohlcv_collector import collect_all_tokens
from datetime import datetime, timedelta
import time
