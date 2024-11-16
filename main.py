from pyrogram import Client, filters
import tgcrypto
from pyrogram.types import Message
from PIL import Image
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import io
load_dotenv()

# Bot Config
API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
STICKER_ID = os.getenv("sticker_id")

STICKER_WIDTH = 150  # Custom width for the sticker
STICKER_HEIGHT = 150  # Custom height for the sticker

# Temp Paths
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Bot
app = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("Welcome! Send me an image, and I'll apply a predefined sticker to it!")

@app.on_message(filters.photo)
async def handle_image(client, message: Message):
    # Download the image sent by the user
    photo_path = await message.download(file_name=f"{TEMP_DIR}/image_{message.chat.id}.png")
    await message.reply("Applying the sticker to your image...")

    # Download the predefined sticker as a PNG
    sticker_file = await client.download_media(STICKER_ID, file_name=f"{TEMP_DIR}/sticker.png")

    # Open the image and sticker
    user_image = Image.open(photo_path).convert("RGBA")
    sticker = Image.open(sticker_file).convert("RGBA")

    # Resize the sticker to custom dimensions (STICKER_WIDTH x STICKER_HEIGHT)
    sticker = sticker.resize((STICKER_WIDTH, STICKER_HEIGHT), Image.ANTIALIAS)

    # Calculate the position to center the sticker
    center_x = (user_image.width - sticker.width) // 2
    center_y = (user_image.height - sticker.height) // 2
    position = (center_x, center_y)

    # Apply the sticker in the center
    user_image.paste(sticker, position, sticker)

    # Save and send the modified image
    output_path = f"{TEMP_DIR}/output_{message.chat.id}.png"
    user_image.save(output_path)

    await message.reply_photo(output_path)

    # Clean up temporary files
    os.remove(photo_path)
    os.remove(sticker_file)
    os.remove(output_path)

if __name__ == "__main__":
    app.run()