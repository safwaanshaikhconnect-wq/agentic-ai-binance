import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from binance.client import Client

# Load environment variables from .env
load_dotenv()

# ── Credentials ───────────────────────────────────────────
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# ── Connections ───────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
binance = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# ── Tool Functions (Gemini calls these directly) ──────────
def get_balance() -> str:
    """Get Binance spot wallet balances with non-zero amounts"""
    account  = binance.get_account()
    balances = [b for b in account["balances"] if float(b["free"]) > 0]
    return json.dumps(balances)

def get_price(symbol: str) -> str:
    """Get current price of a crypto trading pair e.g. BTCUSDT, ETHUSDT"""
    ticker = binance.get_symbol_ticker(symbol=symbol.upper())
    return json.dumps(ticker)

def get_order_history(symbol: str) -> str:
    """Get last 10 orders for a trading pair"""
    orders = binance.get_all_orders(symbol=symbol.upper(), limit=10)
    return json.dumps(orders, default=str)

def get_ticker_24h(symbol: str) -> str:
    """Get 24 hour price change stats for a symbol"""
    stats = binance.get_ticker(symbol=symbol.upper())
    return json.dumps(stats)

# ── Setup Gemini with Tools ───────────────────────────────
model = genai.GenerativeModel(
    model_name="gemini-pro",
    tools=[get_balance, get_price, get_order_history, get_ticker_24h],
    system_instruction="""You are a crypto trading assistant connected to a live 
    Binance account. Help the user monitor their portfolio, analyze prices, and 
    suggest trades. Always show prices in both USDT and INR (multiply USDT by 84).
    Never place orders without explicit user confirmation."""
)

chat_session = model.start_chat(enable_automatic_function_calling=True)

# ── Main Chat Loop ────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Binance Trading Agent Ready (Powered by Gemini)!")
    print("Type your question or 'quit' to exit\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        if user_input:
            response = chat_session.send_message(user_input)
            print(f"\n🤖 Agent: {response.text}\n")