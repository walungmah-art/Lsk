import logging
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)
router = Router()

from config import OWNER_ID, PREMIUM_USERS, BOT_TOKEN, ADMIN_IDS, USER_STATS
from datetime import datetime

bot = Bot(token=BOT_TOKEN)

@router.message(Command("addp"))
async def addp_handler(msg: Message):
    if msg.from_user.id != OWNER_ID and msg.from_user.id not in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗢𝘄𝗻𝗲𝗿 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = msg.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await msg.answer(
            "<blockquote><code>𝗔𝗱𝗱 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 ⚡</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/addp [userid] [days]</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = int(args[1])
    days = int(args[2])
    
    expiry = datetime.now() + timedelta(days=days)
    PREMIUM_USERS[user_id] = expiry.timestamp()
    
    # Save to file
    try:
        import os
        os.makedirs('/root/3D', exist_ok=True)
        with open('/root/3D/premium_users.json', 'w') as f:
            json.dump(PREMIUM_USERS, f)
        
        expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")
        
        # Notify admin
        await msg.answer(
            "<blockquote><code>𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗔𝗱𝗱𝗲𝗱 ✅</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code>\n"
            f"「❃」 𝗗𝗮𝘆𝘀 : <code>{days}</code>\n"
            f"「❃」 𝗘𝘅𝗽𝗶𝗿𝘆 : <code>{expiry_str}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        
        # Notify user
        try:
            await bot.send_message(
                user_id,
                "<blockquote><code>𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗲𝗱 🎉</code></blockquote>\n\n"
                f"<blockquote>「❃」 𝗣𝗹𝗮𝗻 : <code>{days} Days Premium</code>\n"
                f"「❃」 𝗘𝘅𝗽𝗶𝗿𝘆 : <code>{expiry_str}</code>\n"
                f"「❃」 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>Active ✅</code></blockquote>\n\n"
                "<blockquote>「❃」 𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂 𝗳𝗼𝗿 𝘂𝘀𝗶𝗻𝗴 𝗼𝘂𝗿 𝘀𝗲𝗿𝘃𝗶𝗰𝗲!</blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying user {user_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error saving premium users: {e}")
        await msg.answer(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗮𝘃𝗲</blockquote>",
            parse_mode=ParseMode.HTML
        )

@router.message(Command("info"))
async def info_handler(msg: Message):
    user = msg.from_user
    user_id = user.id
    name = user.first_name
    username = f"@{user.username}" if user.username else "None"
    
    # Check premium status
    if user_id in PREMIUM_USERS:
        expiry_ts = PREMIUM_USERS[user_id]
        now_ts = datetime.now().timestamp()
        if now_ts < expiry_ts:
            days_left = int((expiry_ts - now_ts) / 86400)
            premium_status = f"<code>{days_left} days</code>"
        else:
            premium_status = "<code>Expired</code>"
    else:
        premium_status = "<code>Free</code>"
    
    await msg.answer(
        "<blockquote><code>𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼 ℹ️</code></blockquote>\n\n"
        f"<blockquote>「❃」 𝗡𝗮𝗺𝗲 : <code>{name}</code>\n"
        f"「❃」 𝗨𝘀𝗲𝗿 𝗜𝗗 : <code>{user_id}</code>\n"
        f"「❃」 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲 : <code>{username}</code>\n"
        f"「❃」 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 : {premium_status}</blockquote>",
        parse_mode=ParseMode.HTML
    )

@router.message(Command("rmp"))
async def rmp_handler(msg: Message):
    if msg.from_user.id != OWNER_ID and msg.from_user.id not in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗢𝘄𝗻𝗲𝗿 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = msg.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await msg.answer(
            "<blockquote><code>𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 ⚡</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/rmp [userid]</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = int(args[1])
    
    if user_id not in PREMIUM_USERS:
        await msg.answer(
            "<blockquote><code>𝗡𝗼𝘁 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 ⚠</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    del PREMIUM_USERS[user_id]
    
    # Save to file
    try:
        import os
        os.makedirs('/root/3D', exist_ok=True)
        with open('/root/3D/premium_users.json', 'w') as f:
            json.dump(PREMIUM_USERS, f)
        
        # Notify admin
        await msg.answer(
            "<blockquote><code>𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 ✅</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        
        # Notify user
        try:
            await bot.send_message(
                user_id,
                "<blockquote><code>𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗘𝘅𝗽𝗶𝗿𝗲𝗱 ⚠</code></blockquote>\n\n"
                "<blockquote>「❃」 𝗬𝗼𝘂𝗿 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱\n"
                "「❃」 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 : <code>@xDElwin</code></blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying user {user_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error saving premium users: {e}")
        await msg.answer(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗮𝘃𝗲</blockquote>",
            parse_mode=ParseMode.HTML
        )

@router.message(Command("adm_cmd"))
async def adm_cmd_handler(msg: Message):
    if msg.from_user.id != OWNER_ID and msg.from_user.id not in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗢𝘄𝗻𝗲𝗿 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    await msg.answer(
        "<blockquote><code>𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 ⚡</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁\n"
        "    • <code>/addp [userid] [days]</code> - Add Premium\n"
        "    • <code>/rmp [userid]</code> - Remove Premium</blockquote>\n\n"
        "<blockquote>「❃」 𝗔𝗱𝗺𝗶𝗻 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁 (Owner Only)\n"
        "    • <code>/add_adm [userid]</code> - Add Admin\n"
        "    • <code>/rm_adm [userid]</code> - Remove Admin</blockquote>\n\n"
        "<blockquote>「❃」 𝗕𝗼𝘁 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁\n"
        "    • <code>/stats</code> - View Statistics\n"
        "    • <code>/broad [message]</code> - Broadcast Message\n"
        "    • <code>/adm_cmd</code> - Show Admin Commands</blockquote>",
        parse_mode=ParseMode.HTML
    )

@router.message(Command("add_adm"))
async def add_adm_handler(msg: Message):
    if msg.from_user.id != OWNER_ID:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗢𝘄𝗻𝗲𝗿 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = msg.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await msg.answer(
            "<blockquote><code>𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻 ⚡</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/add_adm [userid]</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = int(args[1])
    
    if user_id in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗔𝗱𝗺𝗶𝗻 ⚠</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    ADMIN_IDS.append(user_id)
    
    # Save to file
    try:
        import os
        os.makedirs('/root/3D', exist_ok=True)
        with open('/root/3D/admin_ids.json', 'w') as f:
            json.dump(ADMIN_IDS, f)
        
        # Notify owner
        await msg.answer(
            "<blockquote><code>𝗔𝗱𝗺𝗶𝗻 𝗔𝗱𝗱𝗲𝗱 ✅</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        
        # Notify user
        try:
            await bot.send_message(
                user_id,
                "<blockquote><code>𝗔𝗱𝗺𝗶𝗻 𝗔𝗰𝗰𝗲𝘀𝘀 𝗚𝗿𝗮𝗻𝘁𝗲𝗱 🎉</code></blockquote>\n\n"
                "<blockquote>「❃」 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗽𝗿𝗼𝗺𝗼𝘁𝗲𝗱 𝘁𝗼 𝗔𝗱𝗺𝗶𝗻\n"
                "「❃」 𝗨𝘀𝗲 <code>/adm_cmd</code> 𝘁𝗼 𝘀𝗲𝗲 𝗮𝗱𝗺𝗶𝗻 𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝘀</blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying user {user_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error saving admin IDs: {e}")
        await msg.answer(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗮𝘃𝗲</blockquote>",
            parse_mode=ParseMode.HTML
        )

@router.message(Command("stats"))
async def stats_handler(msg: Message):
    if msg.from_user.id != OWNER_ID and msg.from_user.id not in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗔𝗱𝗺𝗶𝗻𝘀 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    total_users = len(USER_STATS)
    total_checkouts = sum(u["checkouts"] for u in USER_STATS.values())
    total_charged = sum(u["charged"] for u in USER_STATS.values())
    
    # Get top 5 users by checkouts
    top_users = sorted(USER_STATS.items(), key=lambda x: x[1]["checkouts"], reverse=True)[:5]
    
    response = "<blockquote><code>𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗰𝘀 📊</code></blockquote>\n\n"
    response += f"<blockquote>「❃」 𝗧𝗼𝘁𝗮𝗹 𝗨𝘀𝗲𝗿𝘀 : <code>{total_users}</code>\n"
    response += f"「❃」 𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗲𝗰𝗸𝗼𝘂𝘁𝘀 : <code>{total_checkouts}</code>\n"
    response += f"「❃」 𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 : <code>{total_charged}</code></blockquote>\n\n"
    
    if top_users:
        response += "<blockquote><code>𝗧𝗼𝗽 5 𝗨𝘀𝗲𝗿𝘀 🏆</code></blockquote>\n\n"
        for i, (uid, data) in enumerate(top_users, 1):
            # Check if premium
            is_premium = "Premium ⭐" if uid in PREMIUM_USERS and datetime.now().timestamp() < PREMIUM_USERS[uid] else "Free"
            username = f"@{data['username']}" if data['username'] != "None" else "None"
            
            response += f"<blockquote>「{i}」 <b>{data['name']}</b>\n"
            response += f"    • 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲 : <code>{username}</code>\n"
            response += f"    • 𝗨𝘀𝗲𝗿 𝗜𝗗 : <code>{uid}</code>\n"
            response += f"    • 𝗖𝗵𝗲𝗰𝗸𝗼𝘂𝘁𝘀 : <code>{data['checkouts']}</code>\n"
            response += f"    • 𝗖𝗵𝗮𝗿𝗴𝗲𝗱 : <code>{data['charged']}</code>\n"
            response += f"    • 𝗦𝘁𝗮𝘁𝘂𝘀 : <code>{is_premium}</code></blockquote>\n\n"
    
    await msg.answer(response, parse_mode=ParseMode.HTML)

@router.message(Command("rm_adm"))
async def rm_adm_handler(msg: Message):
    if msg.from_user.id != OWNER_ID:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗢𝘄𝗻𝗲𝗿 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = msg.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await msg.answer(
            "<blockquote><code>𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻 ⚡</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/rm_adm [userid]</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = int(args[1])
    
    if user_id not in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗡𝗼𝘁 𝗔𝗱𝗺𝗶𝗻 ⚠</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    ADMIN_IDS.remove(user_id)
    
    # Save to file
    try:
        import os
        os.makedirs('/root/3D', exist_ok=True)
        with open('/root/3D/admin_ids.json', 'w') as f:
            json.dump(ADMIN_IDS, f)
        
        # Notify owner
        await msg.answer(
            "<blockquote><code>𝗔𝗱𝗺𝗶𝗻 𝗥𝗲𝗺𝗼𝘃𝗲𝗱 ✅</code></blockquote>\n\n"
            f"<blockquote>「❃」 𝗨𝘀𝗲𝗿 : <code>{user_id}</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        
        # Notify user
        try:
            await bot.send_message(
                user_id,
                "<blockquote><code>𝗔𝗱𝗺𝗶𝗻 𝗔𝗰𝗰𝗲𝘀𝘀 𝗥𝗲𝘃𝗼𝗸𝗲𝗱 ⚠</code></blockquote>\n\n"
                "<blockquote>「❃」 𝗬𝗼𝘂𝗿 𝗮𝗱𝗺𝗶𝗻 𝗮𝗰𝗰𝗲𝘀𝘀 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗿𝗲𝗺𝗼𝘃𝗲𝗱</blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying user {user_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error saving admin IDs: {e}")
        await msg.answer(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗮𝘃𝗲</blockquote>",
            parse_mode=ParseMode.HTML
        )



@router.message(Command("broad"))
async def broad_handler(msg: Message):
    if msg.from_user.id != OWNER_ID and msg.from_user.id not in ADMIN_IDS:
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗢𝗻𝗹𝘆 𝗔𝗱𝗺𝗶𝗻𝘀 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "<blockquote><code>𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 📢</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/broad [message]</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    broadcast_msg = args[1]
    user_ids = list(USER_STATS.keys())
    
    if not user_ids:
        await msg.answer(
            "<blockquote><code>𝗡𝗼 𝗨𝘀𝗲𝗿𝘀 ⚠</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗡𝗼 𝘂𝘀𝗲𝗿𝘀 𝘁𝗼 𝗯𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝘁𝗼</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    status_msg = await msg.answer(
        f"<blockquote><code>𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁𝗶𝗻𝗴... 📢</code></blockquote>\n\n"
        f"<blockquote>「❃」 𝗧𝗼𝘁𝗮𝗹 : <code>{len(user_ids)}</code>\n"
        f"「❃」 𝗦𝗲𝗻𝘁 : <code>0</code>\n"
        f"「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 : <code>0</code></blockquote>",
        parse_mode=ParseMode.HTML
    )
    
    sent = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, broadcast_msg, parse_mode=ParseMode.HTML)
            sent += 1
        except Exception as e:
            logger.error(f"Failed to send to {user_id}: {e}")
            failed += 1
        
        # Update every 10 users
        if (sent + failed) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"<blockquote><code>𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁𝗶𝗻𝗴... 📢</code></blockquote>\n\n"
                    f"<blockquote>「❃」 𝗧𝗼𝘁𝗮𝗹 : <code>{len(user_ids)}</code>\n"
                    f"「❃」 𝗦𝗲𝗻𝘁 : <code>{sent}</code>\n"
                    f"「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 : <code>{failed}</code></blockquote>",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
    
    await status_msg.edit_text(
        f"<blockquote><code>𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲 ✅</code></blockquote>\n\n"
        f"<blockquote>「❃」 𝗧𝗼𝘁𝗮𝗹 : <code>{len(user_ids)}</code>\n"
        f"「❃」 𝗦𝗲𝗻𝘁 : <code>{sent}</code>\n"
        f"「❃」 𝗙𝗮𝗶𝗹𝗲𝗱 : <code>{failed}</code></blockquote>",
        parse_mode=ParseMode.HTML
    )
