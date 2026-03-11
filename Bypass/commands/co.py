import time
import logging
import aiohttp
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)
router = Router()

from config import ALLOWED_GROUP, OWNER_ID, ALLOWED_USERS, PREMIUM_USERS, USER_STATS, PROXY_FILE
from functions.co_functions import parse_stripe_checkout
from functions.hybrid_charge import charge_card_hybrid
from functions.charge_functions import init_checkout, parse_card
import json
import os

API_URL = "https://web-production-2f61.up.railway.app"

def load_proxies() -> dict:
    try:
        if os.path.exists(PROXY_FILE):
            with open(PROXY_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_proxies(data: dict):
    with open(PROXY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_user_proxies(user_id: int) -> list:
    proxies = load_proxies()
    user_data = proxies.get(str(user_id), [])
    if isinstance(user_data, str):
        return [user_data] if user_data else []
    return user_data if isinstance(user_data, list) else []

def add_user_proxy(user_id: int, proxy: str):
    proxies = load_proxies()
    user_key = str(user_id)
    if user_key not in proxies:
        proxies[user_key] = []
    elif isinstance(proxies[user_key], str):
        proxies[user_key] = [proxies[user_key]] if proxies[user_key] else []
    
    if proxy not in proxies[user_key]:
        proxies[user_key].append(proxy)
    save_proxies(proxies)

def remove_user_proxy(user_id: int, proxy: str = None):
    proxies = load_proxies()
    user_key = str(user_id)
    if user_key in proxies:
        if proxy is None or proxy.lower() == "all":
            del proxies[user_key]
        else:
            if isinstance(proxies[user_key], list):
                proxies[user_key] = [p for p in proxies[user_key] if p != proxy]
                if not proxies[user_key]:
                    del proxies[user_key]
            elif isinstance(proxies[user_key], str) and proxies[user_key] == proxy:
                del proxies[user_key]
        save_proxies(proxies)
        return True
    return False

def format_proxy(proxy: str) -> str:
    if not proxy:
        return None
    parts = proxy.split(':')
    if len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    elif len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    return None

async def validate_proxy(proxy_str: str, timeout: int = 10) -> dict:
    result = {
        "proxy": proxy_str,
        "status": "❌ Dead",
        "response_time": None,
        "ip": None,
        "country": None,
        "error": None
    }
    
    proxy_url = format_proxy(proxy_str)
    if not proxy_url:
        result["error"] = "Invalid format"
        return result
    
    try:
        start = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://ip-api.com/json",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                elapsed = round((time.perf_counter() - start) * 1000, 2)
                if resp.status == 200:
                    data = await resp.json()
                    result["status"] = "✅ Alive"
                    result["response_time"] = f"{elapsed}ms"
                    result["ip"] = data.get("query")
                    result["country"] = data.get("country")
    except asyncio.TimeoutError:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:50]
    
    return result

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
    
    # Single card mode
    if len(parts) == 2:
        card_str = parts[1]
        card = parse_card(card_str)
        
        if not card:
            await msg.answer(
                "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                "<blockquote>「❃」 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱 𝗳𝗼𝗿𝗺𝗮𝘁</blockquote>",
                parse_mode=ParseMode.HTML
            )
            return
        
        processing_msg = await msg.answer(
            "<blockquote><code>𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 ⏳</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        
        checkout_data = await parse_stripe_checkout(url)
        
        if checkout_data.get("error"):
            await processing_msg.edit_text(
                "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                f"<blockquote>「❃」 {checkout_data.get('error')}</blockquote>",
                parse_mode=ParseMode.HTML
            )
            return
        
        pk = checkout_data.get("pk")
        cs = checkout_data.get("cs")
        
        if not pk or not cs:
            await processing_msg.edit_text(
                "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                "<blockquote>「❃」 𝗖𝗼𝘂𝗹𝗱 𝗻𝗼𝘁 𝗲𝘅𝘁𝗿𝗮𝗰𝘁 𝗣𝗞/𝗖𝗦</blockquote>",
                parse_mode=ParseMode.HTML
            )
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                init_data = await init_checkout(pk, cs)
                
                if "error" in init_data:
                    await processing_msg.edit_text(
                        "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                        f"<blockquote>「❃」 {init_data['error'].get('message', 'Init failed')}</blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                    return
                
                # Get user proxy
                user_proxies = get_user_proxies(msg.from_user.id)
                proxy = format_proxy(user_proxies[0]) if user_proxies else None
                logger.info(f"📋 User proxies: {user_proxies}")
                logger.info(f"🔧 Formatted proxy: {proxy}")
                
                result = await charge_card_hybrid(card, pk, cs, init_data, session, url, proxy)
        except Exception as e:
            logger.error(f"Charge error: {e}")
            await processing_msg.edit_text(
                "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                f"<blockquote>「❃」 {str(e)[:100]}</blockquote>",
                parse_mode=ParseMode.HTML
            )
            return
        
        merchant = checkout_data.get("merchant", "Unknown")
        price = checkout_data.get("price", "0")
        currency = checkout_data.get("currency", "USD")
        product = checkout_data.get("product", "Unknown")
        
        status = result.get("status")
        response_msg = result.get("response")
        elapsed = result.get("time", 0)
        
        if status == "CHARGED":
            status_emoji = "✅"
            status_text = "CHARGED"
            USER_STATS[user_id]["charged"] += 1
            save_stats()
        elif status == "LIVE":
            status_emoji = "✅"
            status_text = "LIVE"
        elif status == "DECLINED":
            status_emoji = "❌"
            status_text = "DECLINED"
        elif status == "3DS FAIL":
            status_emoji = "⚠️"
            status_text = "3DS BYPASS FAILED"
        else:
            status_emoji = "⚠️"
            status_text = status or "ERROR"
        
        response = f"<blockquote><code>「 𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗮𝗿𝗴𝗲 {price} {currency} 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{card_str}</code>\n"
        response += f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>{status_text} {status_emoji}</code>\n"
        response += f"「❃」 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : <code>{response_msg}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗠𝗲𝗿𝗰𝗵𝗮𝗻𝘁 : <code>{merchant}</code>\n"
        response += f"「❃」 𝗣𝗿𝗼𝗱𝘂𝗰𝘁 : <code>{product}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{elapsed}s</code></blockquote>"
        
        await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
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
    
    # Parse checkout first
    checkout_data = await parse_stripe_checkout(url)
    
    if checkout_data.get("error"):
        await processing_msg.edit_text(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            f"<blockquote>「❃」 {checkout_data.get('error')}</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    pk = checkout_data.get("pk")
    cs = checkout_data.get("cs")
    
    if not pk or not cs:
        await processing_msg.edit_text(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗖𝗼𝘂𝗹𝗱 𝗻𝗼𝘁 𝗲𝘅𝘁𝗿𝗮𝗰𝘁 𝗣𝗞/𝗖𝗦</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    results = []
    charged_card = None
    start_time = time.perf_counter()
    
    try:
        async with aiohttp.ClientSession() as session:
            init_data = await init_checkout(pk, cs)
            
            if "error" in init_data:
                await processing_msg.edit_text(
                    "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
                    f"<blockquote>「❃」 {init_data['error'].get('message', 'Init failed')}</blockquote>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            # Get user proxy
            user_proxies = get_user_proxies(msg.from_user.id)
            proxy = format_proxy(user_proxies[0]) if user_proxies else None
            logger.info(f"📋 User proxies (mass): {user_proxies}")
            logger.info(f"🔧 Formatted proxy (mass): {proxy}")
            
            for i, card_str in enumerate(cards, 1):
                card = parse_card(card_str)
                
                if not card:
                    results.append({"card": card_str, "status": "ERROR", "msg": "Invalid format", "time": 0})
                    continue
                
                result = await charge_card_hybrid(card, pk, cs, init_data, session, url, proxy)
                
                status = result.get("status")
                msg_text = result.get("response")
                elapsed = result.get("time", 0)
                
                results.append({"card": card_str, "status": status, "msg": msg_text, "time": elapsed})
                
                # Calculate stats
                charged = sum(1 for r in results if r['status'] == 'CHARGED')
                live = sum(1 for r in results if r['status'] == 'LIVE')
                declined = sum(1 for r in results if r['status'] == 'DECLINED')
                errors = sum(1 for r in results if r['status'] not in ['CHARGED', 'LIVE', 'DECLINED'])
                
                # Update with current card and stats
                try:
                    await processing_msg.edit_text(
                        f"<blockquote><code>「 𝗖𝗵𝗮𝗿𝗴𝗶𝗻𝗴 」</code></blockquote>\n\n"
                        f"<blockquote>「❃」 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀 : <code>{i}/{len(cards)}</code></blockquote>\n\n"
                        f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{card_str}</code>\n"
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
                if status == "CHARGED":
                    charged_card = results[-1]
                    USER_STATS[user_id]["charged"] += 1
                    save_stats()
                    break
    except Exception as e:
        logger.error(f"Mass charge error: {e}")
        await processing_msg.edit_text(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            f"<blockquote>「❃」 {str(e)[:100]}</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    total_time = round(time.perf_counter() - start_time, 2)
    merchant = checkout_data.get("merchant", "Unknown")
    price = checkout_data.get("price", "0")
    currency = checkout_data.get("currency", "USD")
    product = checkout_data.get("product", "Unknown")
    
    # Build final response
    if len(cards) == 1:
        # Single card response
        r = results[0]
        
        if r['status'] == 'CHARGED':
            status_emoji = "✅"
            status_text = "CHARGED"
        elif r['status'] == 'LIVE':
            status_emoji = "✅"
            status_text = "LIVE"
        elif r['status'] == 'DECLINED':
            status_emoji = "❌"
            status_text = "DECLINED"
        else:
            status_emoji = "⚠️"
            status_text = r['status'] or "ERROR"
        
        response = f"<blockquote><code>「 𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗮𝗿𝗴𝗲 {price} {currency} 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{r['card']}</code>\n"
        response += f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>{status_text} {status_emoji}</code>\n"
        response += f"「❃」 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : <code>{r['msg']}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗠𝗲𝗿𝗰𝗵𝗮𝗻𝘁 : <code>{merchant}</code>\n"
        response += f"「❃」 𝗣𝗿𝗼𝗱𝘂𝗰𝘁 : <code>{product}</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{total_time}s</code></blockquote>"
    elif charged_card:
        response = f"<blockquote><code>「 𝗦𝘁𝗿𝗶𝗽𝗲 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 ✅ 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗮𝗿𝗱 : <code>{charged_card['card']}</code>\n"
        response += f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>CHARGED ✅</code>\n"
        response += f"「❃」 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 : <code>{charged_card['msg']}</code></blockquote>\n\n"
        if len(results) > 1:
            response += f"<blockquote>「❃」 𝗧𝗿𝗶𝗲𝗱 : <code>{len(results)}/{len(cards)} cards</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{total_time}s</code></blockquote>"
    else:
        charged = sum(1 for r in results if r['status'] == 'CHARGED')
        live = sum(1 for r in results if r['status'] == 'LIVE')
        declined = sum(1 for r in results if r['status'] == 'DECLINED')
        errors = sum(1 for r in results if r['status'] not in ['CHARGED', 'LIVE', 'DECLINED'])
        
        response = f"<blockquote><code>「 𝗠𝗮𝘀𝘀 𝗖𝗵𝗮𝗿𝗴𝗲 𝗥𝗲𝘀𝘂𝗹𝘁𝘀 」</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 : <code>{charged} ✅</code>\n"
        response += f"「❃」 𝗟𝗶𝘃𝗲 : <code>{live} ✅</code>\n"
        response += f"「❃」 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱 : <code>{declined} ❌</code>\n"
        response += f"「❃」 𝗘𝗿𝗿𝗼𝗿𝘀 : <code>{errors} ⚠️</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 : <code>/co</code>\n"
        response += f"「❃」 𝗧𝗶𝗺𝗲 : <code>{total_time}s</code></blockquote>"
    
    await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)


@router.message(Command("proxy"))
async def proxy_command(msg: Message):
    if not check_access(msg):
        return
    
    args = msg.text.split(maxsplit=1)
    user_id = msg.from_user.id
    
    if len(args) == 1:
        # Show current proxies
        proxies = get_user_proxies(user_id)
        if not proxies:
            await msg.reply(
                "❌ <b>No proxies configured</b>\n\n"
                "<b>Usage:</b>\n"
                "• /proxy add host:port:user:pass\n"
                "• /proxy remove host:port:user:pass\n"
                "• /proxy remove all\n"
                "• /proxy check host:port:user:pass",
                parse_mode=ParseMode.HTML
            )
            return
        
        proxy_list = "\n".join([f"• <code>{p}</code>" for p in proxies])
        await msg.reply(
            f"✅ <b>Your proxies:</b>\n\n{proxy_list}\n\n"
            "<b>Usage:</b>\n"
            "• /proxy add host:port:user:pass\n"
            "• /proxy remove host:port:user:pass\n"
            "• /proxy remove all\n"
            "• /proxy check host:port:user:pass",
            parse_mode=ParseMode.HTML
        )
        return
    
    cmd_parts = args[1].split(maxsplit=1)
    if len(cmd_parts) < 1:
        await msg.reply(
            "<b>Usage:</b>\n"
            "• /proxy add host:port:user:pass\n"
            "• /proxy remove host:port:user:pass\n"
            "• /proxy remove all\n"
            "• /proxy check host:port:user:pass",
            parse_mode=ParseMode.HTML
        )
        return
    
    action = cmd_parts[0].lower()
    
    if action == "add":
        if len(cmd_parts) < 2:
            await msg.reply("Usage: /proxy add host:port:user:pass")
            return
        
        proxy = cmd_parts[1]
        
        # Validate proxy format
        parts = proxy.split(':')
        if len(parts) not in [2, 4]:
            await msg.reply("❌ Invalid format. Use: host:port:user:pass or host:port")
            return
        
        # Check if proxy is alive
        checking_msg = await msg.reply("⏳ Checking proxy...")
        result = await validate_proxy(proxy)
        
        if result["status"] == "✅ Alive":
            add_user_proxy(user_id, proxy)
            await checking_msg.edit_text(
                f"✅ <b>Proxy added successfully!</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Status:</b> {result['status']}\n"
                f"<b>Response Time:</b> {result['response_time']}\n"
                f"<b>IP:</b> <code>{result['ip']}</code>\n"
                f"<b>Country:</b> {result['country']}",
                parse_mode=ParseMode.HTML
            )
        else:
            error_msg = f" ({result['error']})" if result['error'] else ""
            await checking_msg.edit_text(
                f"❌ <b>Proxy is dead{error_msg}</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Status:</b> {result['status']}",
                parse_mode=ParseMode.HTML
            )
    
    elif action == "check":
        if len(cmd_parts) < 2:
            await msg.reply("Usage: /proxy check host:port:user:pass")
            return
        
        proxy = cmd_parts[1]
        checking_msg = await msg.reply("⏳ Checking proxy...")
        result = await validate_proxy(proxy)
        
        if result["status"] == "✅ Alive":
            await checking_msg.edit_text(
                f"<b>Proxy Status:</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Status:</b> {result['status']}\n"
                f"<b>Response Time:</b> {result['response_time']}\n"
                f"<b>IP:</b> <code>{result['ip']}</code>\n"
                f"<b>Country:</b> {result['country']}",
                parse_mode=ParseMode.HTML
            )
        else:
            error_msg = f" ({result['error']})" if result['error'] else ""
            await checking_msg.edit_text(
                f"<b>Proxy Status:</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Status:</b> {result['status']}{error_msg}",
                parse_mode=ParseMode.HTML
            )
    
    elif action == "remove":
        if len(cmd_parts) < 2:
            await msg.reply("Usage: /proxy remove host:port:user:pass or /proxy remove all")
            return
        
        proxy = cmd_parts[1]
        if remove_user_proxy(user_id, proxy):
            await msg.reply(f"✅ Proxy removed: <code>{proxy}</code>", parse_mode=ParseMode.HTML)
        else:
            await msg.reply("❌ Proxy not found")
    
    else:
        await msg.reply(
            "<b>Usage:</b>\n"
            "• /proxy add host:port:user:pass\n"
            "• /proxy remove host:port:user:pass\n"
            "• /proxy remove all\n"
            "• /proxy check host:port:user:pass",
            parse_mode=ParseMode.HTML
        )
