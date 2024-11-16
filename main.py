from pyrogram import Client, filters
import TgCrypto
from pyrogram.types import Message
from PIL import Image
import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

# Bot Config
API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")

# MongoDB Config
MONGO_URI = os.getenv("mongo_uri")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["sticker_bot_db"]
users_collection = db["users"]

# Initialize Bot
app = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temp Paths
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Command: Start
@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    if not users_collection.find_one({"_id": user_id}):
        users_collection.insert_one({"_id": user_id})
        await message.reply("Welcome! Send me an image and a sticker to apply the sticker on your image!")
    else:
        await message.reply("Welcome back! Send me an image and a sticker to get started!")

# Image Handling
@app.on_message(filters.photo)
async def handle_image(client, message: Message):
    # Download the image
    photo_path = await message.download(file_name=f"{TEMP_DIR}/image_{message.chat.id}.png")
    users_collection.update_one({"_id": message.from_user.id}, {"$set": {"last_image": photo_path}}, upsert=True)
    await message.reply("Image saved! Now send me a sticker to apply it.")

# Sticker Handling
@app.on_message(filters.sticker)
async def handle_sticker(client, message: Message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"_id": user_id})
    
    if not user_data or "last_image" not in user_data:
        await message.reply("Please send an image first before applying a sticker.")
        return

    # Download the sticker
    sticker_path = await message.download(file_name=f"{TEMP_DIR}/sticker_{message.chat.id}.png")

    # Open the saved image and sticker
    image_path = user_data["last_image"]
    user_image = Image.open(image_path).convert("RGBA")
    sticker = Image.open(sticker_path).convert("RGBA")

    # Resize the sticker
    sticker = sticker.resize((user_image.width // 4, user_image.height // 4))

    # Define the position (bottom-right by default)
    position = (user_image.width - sticker.width - 10, user_image.height - sticker.height - 10)

    # Apply the sticker
    user_image.paste(sticker, position, sticker)

    # Save and send the modified image
    output_path = f"{TEMP_DIR}/output_{message.chat.id}.png"
    user_image.save(output_path)

    await message.reply_photo(output_path)

    # Clean up temporary files
    os.remove(image_path)
    os.remove(sticker_path)
    os.remove(output_path)

    # Remove last image from the database
    users_collection.update_one({"_id": user_id}, {"$unset": {"last_image": ""}})

# Run the Bot
if __name__ == "__main__":
    app.run()
