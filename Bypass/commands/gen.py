import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.enums import ParseMode
from random import randint
from datetime import datetime
import re

logger = logging.getLogger(__name__)
router = Router()

from config import ALLOWED_GROUP, OWNER_ID, ALLOWED_USERS, PREMIUM_USERS

buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="𝙍𝙚-𝙂𝙚𝙣 🔄", callback_data="regen")],
    [InlineKeyboardButton(text="𝙀𝙭𝙞𝙩 ⚠", callback_data="exit")]
])

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

def is_luhn_valid(cc: str) -> bool:
    num = list(map(int, str(cc)))
    return sum(num[::-2] + [sum(divmod(d * 2, 10)) for d in num[-2::-2]]) % 10 == 0

def generate_cc(cc_template: str) -> str:
    while True:
        cc_final = ""
        cc_temp = cc_template.ljust(16 if cc_template[0] != "3" else 15, "x")
        for d in cc_temp:
            cc_final += d if d.isdigit() else str(randint(0, 9))
        if is_luhn_valid(cc_final):
            return cc_final

def generate_cards(bin_template: str, quantity: int = 10) -> list:
    parts = re.findall(r'\d+(?:x+)?', bin_template)
    if not parts:
        return []
    
    cc = parts[0]
    mm = parts[1] if len(parts) > 1 else "rnd"
    yy = parts[2] if len(parts) > 2 else "rnd"
    cvv = parts[3] if len(parts) > 3 else "rnd"
    
    current_year = datetime.now().year
    cards = []
    
    for _ in range(quantity):
        gen_cc = generate_cc(cc)
        
        if yy == "rnd":
            gen_yy = str(randint(current_year, current_year + 10))
        else:
            gen_yy = yy if len(yy) == 4 else f"20{yy}"
        
        if mm == "rnd":
            gen_mm = str(randint(1, 12)).zfill(2)
        else:
            gen_mm = mm.zfill(2)
        
        if cvv == "rnd":
            gen_cvv = str(randint(1000, 9999) if gen_cc[0] == "3" else randint(100, 999))
        else:
            gen_cvv = cvv
        
        cards.append(f"{gen_cc}|{gen_mm}|{gen_yy}|{gen_cvv}")
    
    return cards

@router.message(Command("gen"))
async def gen_handler(msg: Message):
    if not check_access(msg):
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗝𝗼𝗶𝗻 𝘁𝗼 𝘂𝘀𝗲 : <code>https://t.me/+Sw15ZeV_gmZiMzc9</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "<blockquote><code>𝗖𝗮𝗿𝗱 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗼𝗿 ⚡</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗨𝘀𝗮𝗴𝗲 : <code>/gen 400002xxxxxxxxxx|10|2024|xxx</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    try:
        cards = generate_cards(args[1], 10)
        if not cards:
            raise ValueError("Invalid format")
        
        formatted_cards = "\n".join([f"<code>{card}</code>" for card in cards])
        
        response = f"<blockquote><code>𝗖𝗮𝗿𝗱𝘀 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 ✅</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗕𝗜𝗡 : <code>{args[1]}</code></blockquote>\n\n"
        response += f"{formatted_cards}\n\n"
        response += f"<blockquote>「❃」 𝗚𝗲𝗻 𝗯𝘆 : <a href='tg://user?id={msg.from_user.id}'>{msg.from_user.first_name}</a></blockquote>"
        
        await msg.answer(response, parse_mode=ParseMode.HTML, reply_markup=buttons)
    except Exception as e:
        await msg.answer(
            "<blockquote><code>𝗘𝗿𝗿𝗼𝗿 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗗𝗲𝘁𝗮𝗶𝗹 : <code>Invalid format. Use: 400002xxxxxxxxxx|10|2024|xxx</code></blockquote>",
            parse_mode=ParseMode.HTML
        )

@router.callback_query(lambda c: c.data == "regen")
async def regen_callback(callback: CallbackQuery):
    text = callback.message.text
    bin_match = re.search(r'𝗕𝗜𝗡 : (.+)', text)
    if not bin_match:
        await callback.answer("Error: BIN not found", show_alert=True)
        return
    
    bin_template = bin_match.group(1).strip()
    
    try:
        cards = generate_cards(bin_template, 10)
        formatted_cards = "\n".join([f"<code>{card}</code>" for card in cards])
        
        response = f"<blockquote><code>𝗖𝗮𝗿𝗱𝘀 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 ✅</code></blockquote>\n\n"
        response += f"<blockquote>「❃」 𝗕𝗜𝗡 : <code>{bin_template}</code></blockquote>\n\n"
        response += f"{formatted_cards}\n\n"
        response += f"<blockquote>「❃」 𝗚𝗲𝗻 𝗯𝘆 : <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.first_name}</a></blockquote>"
        
        await callback.message.edit_text(response, parse_mode=ParseMode.HTML, reply_markup=buttons)
        await callback.answer("Cards regenerated ✅")
    except Exception as e:
        await callback.answer("Error regenerating cards", show_alert=True)

@router.callback_query(lambda c: c.data == "exit")
async def exit_callback(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Deleted ✅")
