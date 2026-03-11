import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

CARD_PATTERN = re.compile(
    r'(\d{15,19})\s*[|:/\\\-\s]\s*(\d{1,2})\s*[|:/\\\-\s]\s*(\d{2,4})\s*[|:/\\\-\s]\s*(\d{3,4})'
)

def parse_card(line: str) -> dict:
    """Parse a single card from text input."""
    line = line.strip()
    if not line:
        logger.debug("Empty line provided to parse_card")
        return None
    
    match = CARD_PATTERN.search(line)
    if not match:
        logger.debug(f"No card pattern found in: {line[:30]}...")
        return None
    
    cc, mm, yy, cvv = match.groups()
    
    mm = mm.zfill(2)
    if int(mm) < 1 or int(mm) > 12:
        logger.debug(f"Invalid month: {mm}")
        return None
    
    if len(yy) == 2:
        yy = "20" + yy
    if len(yy) != 4:
        logger.debug(f"Invalid year length: {yy}")
        return None
    
    logger.debug(f"Successfully parsed card: {cc[:6]}****{cc[-4:]}")
    return {"cc": cc, "mm": mm, "yy": yy, "cvv": cvv}

def parse_cards(text: str) -> list:
    """Parse multiple cards from text input (one per line)."""
    cards = []
    for line in text.strip().split("\n"):
        card = parse_card(line)
        if card:
            cards.append(card)
    
    logger.info(f"Parsed {len(cards)} cards from input")
    return cards

def format_card(card: dict) -> str:
    """Format a card dict into a string."""
    return f"{card['cc']}|{card['mm']}|{card['yy']}|{card['cvv']}"
