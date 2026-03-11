# Telegram Bot - Railway Deployment

Stripe Checkout 3DS Telegram Bot with card generator.

## Features
- Stripe Checkout parser & charger
- Credit card generator with BIN lookup
- Premium user management
- Mass charge support

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

### Environment Variables

Set these in Railway dashboard:

- `BOT_TOKEN` - Your Telegram bot token (required)
- `OWNER_ID` - Your Telegram user ID (optional, default: 7520618222)
- `ALLOWED_GROUP` - Telegram group ID for access (optional, default: -1003681367566)
- `PREMIUM_USERS_JSON` - JSON string of premium users (optional, format: `{"123456789": 1234567890.0}`)

### Commands

- `/start` - Show bot info
- `/co <url>` - Parse Stripe checkout
- `/co <url> <card>` - Charge card
- `/gen <bin>` - Generate cards
- `/info` - Check user status
- `/addp <userid> <days>` - Add premium (owner only)

## Local Development

```bash
pip install -r requirements.txt
python main.py
```
