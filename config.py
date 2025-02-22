import os
from dotenv import load_dotenv

# Load environment variables from .env file in development
load_dotenv()

# Telegram API Credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "sticker_Bot")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "user_preferences")

# Sticker IDs
STICKERS = {
    "pk": "CAACAgUAAxkBAAOiZzOa1iLzvrUf6qKJIFyB2bQMZ1EAAmMPAAJ7VoBVav_8h5kAAXANNgQ",
    "a14": "CAACAgUAAxkBAAPYZzsH8Jil9sZhWnZwp-Ks-s9y-KMAAisOAAL5LGBXIe5Gb0QOhHM2BA",
    "pkw": "CAACAgUAAxkBAAN8Z0iqa3gAAaBF1UNwU5AnoguUI1PhAALBDQAClCN5VYaEt6hzag7gNgQ"
}
