"""
Telegram Trading Bot with periodic portfolio updates
Integrate with Groq-powered trading agent
"""
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from binance.client import Client
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
binance = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store conversation history per user
user_conversations = {}

# ── Tool Definitions (Same as agent.py) ───────────────────
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
        account = binance.get_account()
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

# ── System Prompt ────────────────────────────────────────
SYSTEM_PROMPT = """You are a crypto trading assistant connected to a live Binance account.
Help the user monitor their portfolio and analyse prices.
Always show prices in both USDT and INR (multiply USDT by 84).
Never place orders without explicit user confirmation.
Keep responses concise and clear. Be professional."""

# ── Query Groq with Tool Calling ──────────────────────────
def query_groq(user_message, chat_id):
    """Send query to Groq and execute tools in loop"""
    # Initialize conversation if new user
    if chat_id not in user_conversations:
        user_conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    messages = user_conversations[chat_id]
    messages.append({"role": "user", "content": user_message})
    
    while True:
        response = groq_client.chat.completions.create(
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
                result = execute_tool(tool_call.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # Add assistant response to history
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

# ── Telegram Bot Handlers ─────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        "🚀 Crypto Trading Bot Ready!\n\n"
        "Ask me anything about your Binance portfolio:\n"
        "• How much BTC do I have?\n"
        "• What's the price of BTC?\n"
        "• Show my balance\n\n"
        "Commands:\n"
        "/reset - Clear conversation history\n\n"
        "Portfolio updates every day at 08:00 and 20:00 UTC"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation history"""
    chat_id = update.message.chat_id
    if chat_id in user_conversations:
        del user_conversations[chat_id]
    await update.message.reply_text("✅ Conversation history cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_message = update.message.text
    chat_id = update.message.chat_id
    
    try:
        # Show typing indicator
        await context.bot.send_chat_action(chat_id, "typing")
        
        # Query Groq (maintains conversation history per user)
        response = query_groq(user_message, chat_id)
        
        # Send response (max 4096 chars per Telegram message)
        if len(response) > 4096:
            for chunk in [response[i:i+4000] for i in range(0, len(response), 4000)]:
                await update.message.reply_text(f"🤖 {chunk}")
        else:
            await update.message.reply_text(f"🤖 {response}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error processing request. Please try again.")

async def send_portfolio_update(context: ContextTypes.DEFAULT_TYPE):
    """Send periodic portfolio update"""
    try:
        account = binance.get_account()
        balances = [b for b in account["balances"] if float(b["free"]) > 0]
        
        message = "📊 Portfolio Update - " + datetime.now().strftime("%Y-%m-%d %H:%M UTC") + "\n\n"
        total_btc = 0
        
        for balance in balances:
            symbol = balance["asset"]
            free = float(balance["free"])
            if free > 0:
                message += f"• {symbol}: {free}\n"
                
                # Try to get USD value if not already USD
                if symbol != "USDT":
                    try:
                        ticker = binance.get_symbol_ticker(symbol=f"{symbol}USDT")
                        usd_price = float(ticker["price"])
                        usd_value = free * usd_price
                        inr_value = usd_value * 84
                        message += f"  ≈ ${usd_value:.2f} (~₹{inr_value:.0f})\n"
                    except:
                        pass
        
        if TELEGRAM_CHAT_ID > 0:
            await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            
    except Exception as e:
        logger.error(f"Portfolio update error: {e}")

# ── Main Application ──────────────────────────────────────
def main():
    """Start the bot"""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Setup scheduler for periodic updates (08:00 and 20:00 UTC)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_portfolio_update,
        trigger="cron",
        hour="8,20",
        minute="0",
        args=[app]
    )
    scheduler.start()
    
    # Start bot
    logger.info("🚀 Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
