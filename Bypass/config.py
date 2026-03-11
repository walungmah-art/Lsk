# Bot Configuration
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8423898751:AAFfYVqmfR2aYQU8uShnw3hGeFcwGZH6qE4")
ALLOWED_GROUP = int(os.getenv("ALLOWED_GROUP", "-1002962582903"))
OWNER_ID = int(os.getenv("OWNER_ID", "7622959338"))
ADMIN_IDS = []  # Admin user IDs
ALLOWED_USERS = []  # Add user IDs here: [123456789, 987654321]
PREMIUM_USERS = {}  # {user_id: expiry_timestamp}
USER_STATS = {}  # {user_id: {"name": "", "username": "", "checkouts": 0, "charged": 0}}
PROXY_FILE = "proxies.json"
