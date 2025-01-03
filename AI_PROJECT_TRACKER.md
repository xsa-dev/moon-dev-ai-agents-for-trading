# 🌙 Moon Dev AI Agents for Trading - Project Tracker 🤖

> 🤖 **AI TRANSCRIPT NOTE**: This document serves as a living transcript for AI agents. Each update helps guide the AI's understanding of project progress and goals.

## 🎯 Project Overview
This is an experimental research project exploring AI agents for trading, developed by Moon Dev. The project aims to complement human trading operations by addressing common challenges like emotional trading, inconsistent execution, and risk management through specialized AI agents.

## 🔍 Current Project State
**Status**: Active Development Phase 🚀
**Last Updated**: 2024-03-21

## 🤖 Current Agent Components
1. **Trading Agent** (trading_agent.py)
   - Status: ✅ Basic Implementation Complete
   - Features:
     - OHLCV data collection and analysis
     - AI-powered buy/sell decisions
     - Position size management
     - Market execution with slippage control
     - Multi-token monitoring
     - Configurable run intervals
     - Transaction retry logic
     - Customizable trading prompts
     - Portfolio allocation logic

2. **Risk Agent** (risk_agent.py)
   - Status: ✅ Basic Implementation Complete
   - Features:
     - Daily PnL monitoring and logging
     - Max loss/gain limit enforcement
     - AI-powered override decisions
     - Portfolio value tracking
     - Position closing functionality
     - Configurable check intervals
     - Runs before and after trading agent
     - Balance history logging
     - Spam token filtering

## 📊 Current Capabilities
- Environment-based configuration
- Secure API key management
- Two-agent system working in tandem:
  - Trading Agent for market analysis and execution
  - Risk Agent for portfolio protection
- Temporary and permanent data storage options
- Multi-token monitoring
- AI-powered trading decisions
- Portfolio balance logging
- Position size management
- Configurable risk limits

## ⚠️ Important Notes
- Using .env for secure key management
- Risk agent runs before and after trading agent
- Configurable sleep intervals between runs
- Max loss/gain limits with AI override capability
- Trading agent only runs if risk agent approves
- Each agent has its own specialized AI prompt

## 🔄 Daily Updates
### 2024-03-21
- Completed risk agent implementation
- Integrated risk and trading agent coordination
- Added portfolio balance tracking
- Added configurable run intervals
- Enhanced error handling and logging
- Added spam token filtering
- Improved position management

## 🎯 Next Steps
1. Enhance risk agent market data analysis
2. Add percentage-based max loss/tp
3. Improve trading agent strategy
4. Add more sophisticated entry/exit logic
5. Implement portfolio-wide analysis

## 🛠️ Technical Stack
- Python-based implementation
- Environment variable configuration
- Temporary and permanent data storage
- Birdeye API integration
- Jupiter API for trading
- Claude AI integration
- Emoji-rich debugging 🌙

## 🌟 Easter Eggs
Throughout the codebase, you'll find Moon Dev's signature touches:
- 🌙 Moon-themed debug messages
- Encouraging comments from Moon Dev
- Space-themed variable names
- Hidden thank you messages to the community

*Last updated by Moon Dev AI Assistant* 🤖✨ 