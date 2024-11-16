from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import tgcrypto
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
PK_STICKER_ID = os.getenv("pk_sticker_id")
A14_STICKER_ID = os.getenv("a14_sticker_id")

STICKER_WIDTH = 260
STICKER_HEIGHT = 160

# Temp Paths
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Bot
app = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user's image paths temporarily
user_images = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("Welcome! Send me an image, and I'll let you choose which sticker to apply!")

@app.on_message(filters.photo)
async def handle_image(client, message: Message):
    # Download the image sent by the user
    photo_path = await message.download(file_name=f"{TEMP_DIR}/image_{message.chat.id}.png")
    
    # Store the image path for this user
    user_images[message.chat.id] = photo_path

    # Create inline keyboard with sticker options
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("PK Sticker", callback_data="sticker_pk"),
            InlineKeyboardButton("A14 Sticker", callback_data="sticker_a14")
        ]
    ])

    await message.reply(
        "Please choose which sticker you want to apply:",
        reply_markup=keyboard
    )

@app.on_callback_query()
async def handle_sticker_choice(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    
    # Check if user has an image stored
    if chat_id not in user_images:
        await callback_query.answer("Please send an image first!", show_alert=True)
        return

    # Get the stored image path
    photo_path = user_images[chat_id]
    
    # Determine which sticker was chosen
    sticker_id = PK_STICKER_ID if callback_query.data == "sticker_pk" else A14_STICKER_ID
    
    await callback_query.message.edit_text("Applying the selected sticker to your image...")

    # Download the chosen sticker
    sticker_file = await client.download_media(sticker_id, file_name=f"{TEMP_DIR}/sticker_{chat_id}.png")

    # Open the image and sticker
    user_image = Image.open(photo_path).convert("RGBA")
    sticker = Image.open(sticker_file).convert("RGBA")

    # Resize the sticker to custom dimensions
    sticker = sticker.resize((STICKER_WIDTH, STICKER_HEIGHT), Image.LANCZOS)

    # Calculate the position to center the sticker
    center_x = (user_image.width - sticker.width) // 2
    center_y = (user_image.height - sticker.height) // 2
    position = (center_x, center_y)

    # Apply the sticker in the center
    user_image.paste(sticker, position, sticker)

    # Save and send the modified image
    output_path = f"{TEMP_DIR}/output_{chat_id}.png"
    user_image.save(output_path)

    await callback_query.message.reply_photo(output_path)

    # Clean up temporary files
    os.remove(photo_path)
    os.remove(sticker_file)
    os.remove(output_path)
    del user_images[chat_id]  # Remove stored image path

    await callback_query.answer()

if __name__ == "__main__":
    app.run()