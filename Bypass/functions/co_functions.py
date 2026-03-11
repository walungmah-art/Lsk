import re
import logging
import aiohttp
import base64
from urllib.parse import unquote

# Configure logging
logger = logging.getLogger(__name__)

HEADERS = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://checkout.stripe.com",
    "referer": "https://checkout.stripe.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def escape_md(text: str) -> str:
    if not text:
        return ""
    special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in special:
        text = text.replace(c, f'\\{c}')
    return text

def extract_checkout_url(text: str) -> str:
    patterns = [
        r'https?://checkout\.stripe\.com/c/pay/cs_[^\s\"\'\<\>\)]+',
        r'https?://checkout\.stripe\.com/[^\s\"\'\<\>\)]+',
        r'https?://buy\.stripe\.com/[^\s\"\'\<\>\)]+',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            url = m.group(0).rstrip('.,;:')
            return url
    return None

def decode_pk_from_url(url: str) -> dict:
    """Extract PK and CS from Stripe checkout URL hash fragment using XOR decoding"""
    result = {"pk": None, "cs": None, "site": None}
    
    try:
        cs_match = re.search(r'cs_(live|test)_[A-Za-z0-9]+', url)
        if cs_match:
            result["cs"] = cs_match.group(0)
        
        if '#' not in url:
            return result
        
        hash_part = url.split('#')[1]
        hash_decoded = unquote(hash_part)
        
        try:
            decoded_bytes = base64.b64decode(hash_decoded)
            xored = ''.join(chr(b ^ 5) for b in decoded_bytes)
            
            pk_match = re.search(r'pk_(live|test)_[A-Za-z0-9]+', xored)
            if pk_match:
                result["pk"] = pk_match.group(0)
            
            site_match = re.search(r'https?://[^\s\"\'\<\>]+', xored)
            if site_match:
                result["site"] = site_match.group(0)
        except:
            pass
            
    except Exception as e:
        pass
    
    return result

async def parse_stripe_checkout(url: str) -> dict:
    result = {
        "url": url,
        "pk": None,
        "cs": None,
        "merchant": None,
        "price": None,
        "currency": None,
        "product": None,
        "country": None,
        "mode": None,
        "customer_name": None,
        "customer_email": None,
        "support_email": None,
        "support_phone": None,
        "cards_accepted": None,
        "success_url": None,
        "cancel_url": None,
        "error": None
    }
    
    try:
        decoded = decode_pk_from_url(url)
        result["pk"] = decoded.get("pk")
        result["cs"] = decoded.get("cs")
        
        if result["pk"] and result["cs"]:
            async with aiohttp.ClientSession() as session:
                body = f"key={result['pk']}&eid=NA&browser_locale=en-US&redirect_type=url"
                async with session.post(
                    f"https://api.stripe.com/v1/payment_pages/{result['cs']}/init",
                    headers=HEADERS,
                    data=body
                ) as r:
                    init_data = await r.json()
                
                if "error" not in init_data:
                    acc = init_data.get("account_settings", {})
                    result["merchant"] = acc.get("display_name") or acc.get("business_name")
                    result["support_email"] = acc.get("support_email")
                    result["support_phone"] = acc.get("support_phone")
                    result["country"] = acc.get("country")
                    
                    lig = init_data.get("line_item_group")
                    inv = init_data.get("invoice")
                    if lig:
                        result["price"] = lig.get("total", 0) / 100
                        result["currency"] = lig.get("currency", "").upper()
                        if lig.get("line_items"):
                            result["product"] = lig["line_items"][0].get("name")
                    elif inv:
                        result["price"] = inv.get("total", 0) / 100
                        result["currency"] = inv.get("currency", "").upper()
                    
                    mode = init_data.get("mode", "")
                    if mode:
                        result["mode"] = mode.upper()
                    elif init_data.get("subscription"):
                        result["mode"] = "SUBSCRIPTION"
                    else:
                        result["mode"] = "PAYMENT"
                    
                    cust = init_data.get("customer") or {}
                    result["customer_name"] = cust.get("name")
                    result["customer_email"] = init_data.get("customer_email") or cust.get("email")
                    
                    pm_types = init_data.get("payment_method_types") or []
                    if pm_types:
                        cards = [t.upper() for t in pm_types if t != "card"]
                        if "card" in pm_types:
                            cards.insert(0, "CARD")
                        result["cards_accepted"] = ", ".join(cards) if cards else "CARD"
                    
                    result["success_url"] = init_data.get("success_url")
                    result["cancel_url"] = init_data.get("cancel_url")
                else:
                    result["error"] = init_data.get("error", {}).get("message", "Init failed")
        else:
            result["error"] = "Could not decode PK/CS from URL"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result
    result = {
        "url": url,
        "pk": None,
        "cs": None,
        "merchant": None,
        "price": None,
        "currency": None,
        "product": None,
        "error": None
    }
    
    try:
        decoded = decode_pk_from_url(url)
        result["pk"] = decoded.get("pk")
        result["cs"] = decoded.get("cs")
        
        if result["pk"] and result["cs"]:
            async with aiohttp.ClientSession() as session:
                body = f"key={result['pk']}&eid=NA&browser_locale=en-US&redirect_type=url"
                async with session.post(
                    f"https://api.stripe.com/v1/payment_pages/{result['cs']}/init",
                    headers=HEADERS,
                    data=body
                ) as r:
                    init_data = await r.json()
                
                if "error" not in init_data:
                    acc = init_data.get("account_settings", {})
                    result["merchant"] = acc.get("display_name") or acc.get("business_name")
                    result["country"] = acc.get("country")
                    result["support_email"] = acc.get("support_email")
                    result["phone"] = acc.get("support_phone")
                    
                    lig = init_data.get("line_item_group")
                    inv = init_data.get("invoice")
                    if lig:
                        result["price"] = lig.get("total", 0) / 100
                        result["currency"] = lig.get("currency", "").upper()
                        result["mode"] = lig.get("mode", "").upper()
                    elif inv:
                        result["price"] = inv.get("total", 0) / 100
                        result["currency"] = inv.get("currency", "").upper()
                    
                    if lig and lig.get("line_items"):
                        result["product"] = lig["line_items"][0].get("name")
                else:
                    result["error"] = init_data.get("error", {}).get("message", "Init failed")
                    
                    pm_types = init_data.get("payment_method_types") or []
                    if pm_types:
                        cards = [t.upper() for t in pm_types if t != "card"]
                        if "card" in pm_types:
                            cards.insert(0, "CARD")
                        result["cards_accepted"] = ", ".join(cards) if cards else "CARD"
                    
                    result["success_url"] = init_data.get("success_url")
                    result["cancel_url"] = init_data.get("cancel_url")
                    
                    cust = init_data.get("customer") or {}
                    result["customer_name"] = cust.get("name")
                    result["customer_email"] = init_data.get("customer_email") or cust.get("email")
                    
                    mode = init_data.get("mode", "")
                    if mode:
                        result["mode"] = mode.upper()
                    elif init_data.get("subscription"):
                        result["mode"] = "SUBSCRIPTION"
                    else:
                        result["mode"] = "PAYMENT"
        else:
            result["error"] = "Could not decode PK/CS from URL"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def format_checkout_md(data: dict) -> str:
    if data.get("error"):
        return f"❌ `{escape_md(data['error'])}`"
    
    lines = ["⚡ *Stripe Checkout*", ""]
    
    if data.get("merchant"):
        lines.append(f"🏪 *Merchant:* `{escape_md(data['merchant'])}`")
    
    if data.get("product"):
        lines.append(f"📦 *Product:* `{escape_md(data['product'][:50])}`")
    
    if data.get("price"):
        sym = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}.get(data.get("currency", ""), "")
        lines.append(f"💰 *Price:* `{sym}{data['price']:.2f} {data.get('currency', '')}`")
    
    lines.append("")
    
    if data.get("pk"):
        lines.append(f"🔑 *PK:* `{escape_md(data['pk'][:30])}...`")
    
    if data.get("cs"):
        lines.append(f"🎫 *CS:* `{escape_md(data['cs'][:30])}...`")
    
    return "\n".join(lines)

def add_blockquote(text: str) -> str:
    return "\n".join(f">{line}" for line in text.split("\n"))
