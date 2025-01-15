from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, FileResponse, Response
import logging
from config import CSV_DIRECTORY
from utils import load_api_keys, rate_limiter, create_api_key
from chains.solana.rpc_interface import RPCInterface, MOON_WALLET
import json
import traceback
import pandas as pd
import os
from collections import deque

# Add AFI imports
import sys
sys.path.append('/root/algos/api/afi-rag')
import main as afi_system
from generator import generate_response
from afi_calls import handle_afi_ask, check_afi_health

# Initialize RPC interface
rpc = RPCInterface()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API keys
api_keys = load_api_keys()

# Create FastAPI app
app = FastAPI(title="MoonDev's Solana AI Platform 🌙")

# Update the CSV directory configuration to handle multiple directories
COPYBOT_CSV_DIRECTORY = '/root/algos/copy_bot/data'

async def validate_api_key(api_key: str = Header(..., alias="X-API-Key")):
    logging.debug(f"Validating API Key: {api_key}")
    print(f"🔑 Received API Key: {api_key[:8]}...")  # Debug line
    
    # Load fresh API keys
    api_keys = load_api_keys()
    
    if api_key not in api_keys:
        logging.debug("Invalid API Key")
        print(f"❌ API Key not found in valid keys")  # Debug line
        print(f"🔍 Valid keys: {list(api_keys.keys())[:5]}...")  # Show first few valid keys
        raise HTTPException(
            status_code=403,
            detail="No API key access, get one at https://algotradecamp.com"
        )
    
    # Try rate limit check up to 3 times with delays
    for attempt in range(3):
        if rate_limiter(api_key):
            logging.debug("API Key validated successfully")
            print("✅ API Key validated successfully")  # Debug line
            return api_key
        else:
            import asyncio
            delay = (attempt + 1) * 2  # 2, 4, 6 seconds
            print(f"🌙 MoonDev Rate Limit Hit - Sleeping for {delay}s (attempt {attempt + 1}/3)")
            await asyncio.sleep(delay)
    
    # If we still hit rate limit after retries
    logging.debug("Rate limit exceeded for API Key after retries")
    raise HTTPException(status_code=429, detail="Rate limit exceeded after retries")

@app.get("/")
@app.get("/")
async def root():
    return {
        "message": "Welcome to MoonDev's Multi-Chain AI Platform! 🌙",
        "supported_chains": ["solana"],
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "afi": {  # Add AFI endpoints
                "ask": "/afi/ask",
                "health": "/afi/health"
            },
            "csv": {
                "list": "/list-csvs",
                "get": "/files/{filename}?limit=1000",
                "legacy_get": "/get-csv/{filename}"
            },
            "solana": {
                "price": "/chains/solana/token_price/{token_address}",
                "balance": "/chains/solana/wallet_balance/{wallet_address}",
                "my_balance": "/chains/solana/wallet_balance",
                "transactions": "/chains/solana/wallet/{wallet_address}/transactions"
            },
            "copybot": {
                "follow_list": "/copybot/data/follow_list",
                "recent_transactions": "/copybot/data/recent_txs"
            }
        }
    }

# AFI Endpoints
@app.post("/afi/ask")
async def ask_afi(
    question: str,
    temperature: float = 0.7,
    api_key: str = Header(..., alias="X-API-Key")
):
    """🤖 Ask AFI about trading strategies"""
    await validate_api_key(api_key)
    return await handle_afi_ask(question, temperature, api_key)

@app.get("/afi/health")
async def afi_health_check(api_key: str = Header(..., alias="X-API-Key")):
    """💓 Check AFI System Health"""
    await validate_api_key(api_key)
    return await check_afi_health()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "MoonDev's systems are operational! 🚀",
        "chains": {
            "solana": "active"
        }
    }

@app.get("/chains/solana/token_price/{token_address}")
async def get_solana_token_price(token_address: str, api_key: str = Header(..., alias="X-API-Key")):
    await validate_api_key(api_key)
    try:
        result = await rpc.get_token_price(token_address)
        
        # Check if we got a valid price
        if result.get('error'):
            print(f"❌ Price fetch error for {token_address}: {result['error']}")
            return {
                "success": False,
                "token_address": token_address,
                "price": None,
                "error": result['error']
            }
            
        # Extract price data
        price_data = result.get('data', {}).get(token_address, {})
        if not price_data or 'price' not in price_data:
            print(f"ℹ️ No price data available for token: {token_address}")
            return {
                "success": True,
                "token_address": token_address,
                "price": None,
                "message": "No price data available"
            }
            
        # Convert price to float and format response
        try:
            price_value = float(price_data['price'])
            print(f"✨ Price found for {token_address}: {price_value}")
            return {
                "success": True,
                "token_address": token_address,
                "price": price_value,
                "message": "🌙 MoonDev price fetch successful!"
            }
        except (ValueError, TypeError) as e:
            print(f"❌ Error converting price value: {str(e)}")
            return {
                "success": False,
                "token_address": token_address,
                "price": None,
                "error": "Invalid price format"
            }
            
    except Exception as e:
        print(f"❌ Unexpected error in price fetch: {str(e)}")
        return {
            "success": False,
            "token_address": token_address,
            "price": None,
            "error": str(e)
        }

@app.get("/chains/solana/wallet_balance/{wallet_address}")
async def get_solana_wallet_balance(wallet_address: str, api_key: str = Header(..., alias="X-API-Key")):
    await validate_api_key(api_key)
    result = await rpc.get_wallet_balance(wallet_address)
    return result

@app.get("/chains/solana/wallet_balance")
async def get_solana_wallet_balance_default(api_key: str = Header(..., alias="X-API-Key")):
    await validate_api_key(api_key)
    result = await rpc.get_wallet_balance(MOON_WALLET)
    return result

@app.get("/chains/solana/wallet/{wallet_address}/transactions")
async def get_solana_wallet_transactions(
    wallet_address: str, 
    limit: int = 100,
    api_key: str = Header(..., alias="X-API-Key")
):
    print("\n" + "="*50)
    print("🔍 TRANSACTION ANALYSIS DETAILS")
    print("="*50)
    print(f"🔑 API Key: {api_key[:8]}...")
    print(f"👛 Wallet: {wallet_address}")
    print(f"🔢 Requested trades: {limit}")
    
    await validate_api_key(api_key)
    
    try:
        print("\n📝 TRANSACTION ANALYSIS:")
        print("-"*50)
        
        # Keep fetching until we have enough real trades
        trades_found = 0
        all_trades = []
        batch_size = limit * 2  # Request more transactions than needed to account for non-trades
        
        while trades_found < limit:
            # Get batch of transactions
            result = await rpc.get_wallet_transactions(wallet_address, batch_size)
            
            if not result.get('data', {}).get('solana'):
                print("❌ No more transactions found")
                break
                
            for tx in result['data']['solana']:
                if tx['txHash'] not in [t['txHash'] for t in all_trades]:  # Avoid duplicates
                    print(f"\n🔍 Processing transaction: {tx['txHash'][:12]}...")
                    print(f"⏰ Time: {tx['datetime']}")
                    print(f"💰 Fee: {tx['fee']} SOL")
                    print(f"📥 Buy: {tx['buy_amount']} of {tx['buy_token']}")
                    print("-"*30)
                    
                    trades_found += 1
                    all_trades.append(tx)
                    
                    if trades_found >= limit:
                        break
            
            if trades_found < limit:
                batch_size *= 2  # Double batch size if we need more trades
                print(f"🔄 Need more trades. Increasing batch size to {batch_size}")
                
        print(f"\n✨ Found {trades_found} valid trades")
        
        final_result = {
            'success': True,
            'data': {
                'solana': all_trades[:limit]  # Ensure we don't return more than requested
            }
        }
        
        print("\n📊 FINAL RESULT:")
        print("-"*50)
        print(json.dumps(final_result, indent=2))
        print("="*50)
        return final_result
        
    except Exception as e:
        print(f"\n❌ ERROR OCCURRED:")
        print("-"*50)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(traceback.format_exc())
        print("="*50)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-csvs")
async def list_csvs():
    print("🗂️ MoonDev CSV List Request")
    try:
        # Use absolute path for CSV directory
        CSV_DIRECTORY = '/root/algos/liqs_oi_funding/data'
        files = [f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')]
        print(f"📁 Found CSV files: {files}")
        return files  # Return direct list without JSONResponse wrapper
    except Exception as e:
        print(f"❌ Error listing CSVs: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/files/{filename}")
async def get_csv(filename: str, limit: int = None):
    print(f"📊 MoonDev CSV Request: {filename}")
    print(f"📏 Requested limit: {limit}")
    
    try:
        filepath = os.path.join(CSV_DIRECTORY, filename)
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return JSONResponse(
                status_code=404,
                content={"error": "File not found."}
            )

        # For direct file streaming (like your original server)
        if not limit:
            print("📄 Streaming full file directly")
            return FileResponse(filepath, media_type='text/csv')
            
        # For limited data
        with open(filepath, 'r') as f:
            header = f.readline()  # Skip header
            lines = deque(f.readlines(), limit)
            contents = header + ''.join(lines)
            print(f"✨ Successfully loaded {len(lines)} rows")
            return Response(content=contents, media_type='text/csv')
        
    except Exception as e:
        print(f"❌ Error processing CSV: {str(e)}")
        print(f"🔍 Full error traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/get-csv/{filename}")
async def get_csv_legacy(filename: str):
    print(f"📊 MoonDev Legacy CSV Request: {filename}")
    
    try:
        if filename not in os.listdir(CSV_DIRECTORY):
            print(f"❌ File not found: {filename}")
            return JSONResponse(
                status_code=404,
                content={"error": "File not found."}
            )
            
        filepath = os.path.join(CSV_DIRECTORY, filename)
        df = pd.read_csv(filepath)
        print(f"✨ Successfully loaded CSV with {len(df)} rows")
        return JSONResponse(content=df.to_dict(orient='records'))
        
    except Exception as e:
        print(f"❌ Error processing CSV: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Add new copybot endpoints
@app.get("/copybot/data/follow_list")
async def get_follow_list(api_key: str = Header(..., alias="X-API-Key")):
    """Get the current follow list for copy trading"""
    print("📋 Moon Dev CopyBot: Fetching follow list...")
    await validate_api_key(api_key)
    
    try:
        # Use absolute path for testing
        filepath = '/root/algos/copy_bot/data/follow_list.csv'
        
        if not os.path.exists(filepath):
            print(f"❌ Follow list file not found at: {filepath}")
            return JSONResponse(
                status_code=404,
                content={"error": f"Follow list not found at {filepath}"}
            )
            
        print(f"✨ Streaming follow list from: {filepath}")
        return FileResponse(
            path=filepath,
            media_type='text/csv',
            filename='follow_list.csv'
        )
        
    except Exception as e:
        print(f"❌ Error loading follow list: {str(e)}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/copybot/data/recent_txs")
async def get_recent_transactions(api_key: str = Header(..., alias="X-API-Key")):
    """Get recent transactions from copy trading"""
    print("🔄 Moon Dev CopyBot: Fetching recent transactions...")
    await validate_api_key(api_key)
    
    try:
        # Use absolute path for testing
        filepath = '/root/algos/copy_bot/data/recent_txs.csv'
        
        if not os.path.exists(filepath):
            print(f"❌ Recent transactions file not found at: {filepath}")
            return JSONResponse(
                status_code=404,
                content={"error": f"Recent transactions not found at {filepath}"}
            )
            
        print(f"✨ Streaming recent transactions from: {filepath}")
        return FileResponse(
            path=filepath,
            media_type='text/csv',
            filename='recent_txs.csv'
        )
        
    except Exception as e:
        print(f"❌ Error loading recent transactions: {str(e)}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)