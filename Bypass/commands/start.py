import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

router = Router()

# Import from config
from config import ALLOWED_GROUP, OWNER_ID, ALLOWED_USERS, PREMIUM_USERS

exit_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="𝙀𝙭𝙞𝙩 ⚠", callback_data="exit_start")]
])

def check_access(msg: Message) -> bool:
    """Check if user has access to the bot commands."""
    if not msg.from_user:
        logger.warning("Access denied: No user information in message")
        return False
    
    user_id = msg.from_user.id
    
    # Owner always has access (private, group, anywhere)
    if user_id == OWNER_ID:
        logger.debug(f"Access granted to owner: {user_id}")
        return True
    
    # Check whitelist
    if user_id in ALLOWED_USERS:
        logger.debug(f"Access granted to whitelisted user: {user_id}")
        return True
    
    # Check premium users with expiry
    if user_id in PREMIUM_USERS:
        from datetime import datetime
        if datetime.now().timestamp() < PREMIUM_USERS[user_id]:
            logger.debug(f"Access granted to premium user: {user_id}")
            return True
    
    # Log chat ID for debugging
    logger.info(f"User {user_id} trying to access from chat {msg.chat.id}")
    
    # Allow if user is in the allowed group
    if msg.chat.id == ALLOWED_GROUP:
        logger.debug(f"Access granted to group member: {user_id}, chat: {msg.chat.id}")
        return True
    
    logger.warning(f"Access denied for user {user_id} in chat {msg.chat.id}")
    return False

@router.message(Command("start"))
async def start_handler(msg: Message):
    if not check_access(msg):
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗙𝗼𝗿 𝗔𝗰𝗰𝗲𝘀𝘀 : <code>@xDElwin</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗝𝗼𝗶𝗻 𝘁𝗼 𝘂𝘀𝗲 : <code>https://t.me/+Sw15ZeV_gmZiMzc9</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    welcome = (
        "<blockquote><code>Elwin Hitter ⚡</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗵𝗲𝗰𝗸𝗼𝘂𝘁 𝗣𝗮𝗿𝘀𝗲𝗿\n"
        "    • <code>/co url</code> - <code>Parse Stripe Checkout</code>\n"
        "    • <code>/co url cc|mm|yy|cvv</code> - <code>Checkout</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗖 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗿\n"
        "    • <code>/gen [ BIN ]</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼\n"
        "    • <code>/info</code> - <code>Check Your Status</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗦𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗨𝗥𝗟𝘀\n"
        "    • <code>checkout.stripe.com</code>\n"
        "    • <code>buy.stripe.com</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 :<code>@xDElwin</code></blockquote>"
    )
    await msg.answer(welcome, parse_mode=ParseMode.HTML, reply_markup=exit_button)

@router.message(Command("help"))
async def help_handler(msg: Message):
    if not check_access(msg):
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗝𝗼𝗶𝗻 𝘁𝗼 𝘂𝘀𝗲 : <code>https://t.me/+Sw15ZeV_gmZiMzc9</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    help_text = (
        "<blockquote><code>𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 📋</code></blockquote>\n\n"
        "<blockquote>「❃」 <code>/start</code> - Show welcome message\n"
        "「❃」 <code>/help</code> - Show this help\n"
        "「❃」 <code>/co url</code> - Parse checkout info\n"
        "「❃」 <code>/co url cards</code> - Charge cards</blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗮𝗿𝗱 𝗙𝗼𝗿𝗺𝗮𝘁 : <code>cc|mm|yy|cvv</code>\n"
        "「❃」 𝗘𝘅𝗮𝗺𝗽𝗹𝗲 : <code>4242424242424242|12|25|123</code></blockquote>"
    )
    await msg.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=exit_button)

@router.callback_query(lambda c: c.data == "exit_start")
async def exit_start_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("𝙈𝙨𝙜 𝘿𝙚𝙡𝙚𝙩𝙚𝙙 ✅")
