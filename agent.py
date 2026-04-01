from groq import Groq
import json
import os
from dotenv import load_dotenv
from binance.client import Client

# Load environment variables from .env
load_dotenv()

# ── Credentials ───────────────────────────────────────────
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# ── Connections ───────────────────────────────────────────
client  = Groq(api_key=GROQ_API_KEY)
binance = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# ── Tool Definitions ──────────────────────────────────────
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Get Binance spot wallet balances with non-zero amounts",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Get current price of a crypto pair e.g. BTCUSDT",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string", "description": "Trading pair e.g. BTCUSDT"}},
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticker_24h",
            "description": "Get 24 hour price change stats for a symbol",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_history",
            "description": "Get last 10 orders for a trading pair",
            "parameters": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"]
            }
        }
    }
]

# ── Tool Executor ─────────────────────────────────────────
def execute_tool(name, args):
    if name == "get_balance":
        account  = binance.get_account()
        balances = [b for b in account["balances"] if float(b["free"]) > 0]
        return json.dumps(balances)
    elif name == "get_price":
        return json.dumps(binance.get_symbol_ticker(symbol=args["symbol"].upper()))
    elif name == "get_ticker_24h":
        return json.dumps(binance.get_ticker(symbol=args["symbol"].upper()))
    elif name == "get_order_history":
        orders = binance.get_all_orders(symbol=args["symbol"].upper(), limit=10)
        return json.dumps(orders, default=str)
    return "Tool not found"

# ── Main Chat Loop ────────────────────────────────────────
SYSTEM_PROMPT = """You are a crypto trading assistant connected to a live Binance account.
Help the user monitor their portfolio and analyse prices.
Always show prices in both USDT and INR (multiply USDT by 84).
Never place orders without explicit user confirmation.
For swing trade suggestions, consider 3-21 day holding periods."""

if __name__ == "__main__":
    print("🚀 Binance Trading Agent Ready (Powered by Groq)!")
    print("Type your question or 'quit' to exit\n")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        while True:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=1024
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tool_call in msg.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    # print(f"\n🔧 Calling: {tool_call.function.name}({args})")
                    result = execute_tool(tool_call.function.name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
            else:
                print(f"\n🤖 Agent: {msg.content}\n")
                messages.append({"role": "assistant", "content": msg.content})
                break