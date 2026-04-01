# Crypto Trading Telegram Bot - Deployment Guide

## 📋 Prerequisites

1. **Groq API Key** - Get from [console.groq.com](https://console.groq.com)
2. **Binance API Keys** - Get from [binance.com/account/api-management](https://www.binance.com/account/api-management)
3. **Telegram Bot Token** - Create via BotFather (@botfather on Telegram)
4. **Python 3.11+**

---

## 🤖 Create Telegram Bot (BotFather)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "MyTradingBot")
4. Choose a username (e.g., "my_trading_bot")
5. Copy the **HTTP API token** (looks like: `123456789:ABCDefgh...`)

## 🆔 Get Your Telegram Chat ID

1. Send a message to your bot (e.g., "Hello")
2. Open this in a browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Replace `<YOUR_BOT_TOKEN>` with your actual token
4. Find `"chat":{"id":123456789}` - that's your CHAT_ID

---

## 🚀 Local Setup & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create .env File
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
GROQ_API_KEY=gsk_xxxxx
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=xxx
TELEGRAM_BOT_TOKEN=123456789:ABCxxx
TELEGRAM_CHAT_ID=987654321
```

### 3. Test Locally
```bash
python telegram_bot.py
```

Send a message to your Telegram bot - it should respond!

---

## 🌐 Deploy to Railway (Free Tier)

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub/Google
- Create a new project

### 2. Connect GitHub Repository
1. Push your code to GitHub
2. In Railway, click "New" → "GitHub Repo"
3. Select your `trading-mcp` repository
4. Authorize Railway

### 3. Add Environment Variables
In Railway dashboard:
1. Go to your project
2. Click "Variables"
3. Add all 5 variables from `.env`:
   - `GROQ_API_KEY`
   - `BINANCE_API_KEY`
   - `BINANCE_API_SECRET`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

4. Click "Deploy"

### 4. Monitor Logs
```bash
# View deployment logs in Railway web UI
#  or via CLI:
railway logs
```

---

## 📅 Portfolio Update Times

The bot sends automatic portfolio updates at:
- **08:00 UTC** (daily morning)
- **20:00 UTC** (daily evening)

To modify times, edit line 160 in `telegram_bot.py`:
```python
scheduler.add_job(
    send_portfolio_update,
    trigger="cron",
    hour="8,20",      # ← Change these hours (24-hour format, UTC)
    minute="0",
    args=[app]
)
```

---

## 💬 Bot Commands

Users can send messages like:
- "How much BTC do I have?"
- "What's the price of Bitcoin?"
- "Show my balance"
- "Get ETH price"

The bot will query your Binance account and respond!

---

## ⚠️ Security Notes

🔒 **NEVER commit `.env` file to GitHub!**
- `.gitignore` already protects it
- Use Railway/Heroku's environment variable system

🔐 **API Keys rotation** (recommended):
- Rotate Groq/Binance keys periodically
- Disable unused IP restrictions on Binance
- Use read-only Binance API keys (no trading permission)

---

## 🐛 Troubleshooting

### Bot not responding
- Check bot token in `.env`
- Verify chat ID is correct
- Check Railway logs: `railway logs`

### Portfolio update not sent
- Check scheduler in logs
- Verify timezone (updates use UTC)
- Ensure TELEGRAM_CHAT_ID is set

### Binance errors
- Verify API key/secret are correct
- Check IP whitelist on Binance
- Ensure spot wallet has balances

---

## 📚 File Structure
```
trading-mcp/
├── telegram_bot.py      # Main bot (handles queries + periodic updates)
├── agent.py             # Original Groq agent (for local testing)
├── server.py            # Gemini agent (alternative)
├── requirements.txt     # Python dependencies
├── .env.example         # Template for credentials
├── .env                 # Actual credentials (in .gitignore)
├── .gitignore          # Prevent credential leaks
├── Procfile            # Deployment config
└── runtime.txt         # Python version
```

---

## 🎯 Next Steps

1. ✅ Create Telegram bot with BotFather
2. ✅ Get Groq + Binance API keys
3. ✅ Create `.env` file locally
4. ✅ Test with `python telegram_bot.py`
5. ✅ Push to GitHub
6. ✅ Deploy on Railway

Enjoy your 24/7 trading bot! 🚀
