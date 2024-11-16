from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import tgcrypto
from PIL import Image
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import io
import asyncio
import time
load_dotenv()

# Bot Config
API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
PK_STICKER_ID = os.getenv("pk_sticker_id")
A14_STICKER_ID = os.getenv("a14_sticker_id")

# Different sizes for each sticker
PK_STICKER_SIZE = (300, 160)  # Width, Height for PK sticker
A14_STICKER_SIZE = (300, 250)  # Width, Height for A14 sticker

# Loading animation frames (rotating hourglass)
LOADING_FRAMES = ["⌛", "⏳"]

# Fade-out and deletion animation frames
FADE_FRAMES = [
    "🌕 {text}",
    "🌔 {text}",
    "🌓 {text}",
    "🌒 {text}",
    "🌑 {text}",
    "⬛️"
]

DELETE_ANIMATIONS = [
    "∎∎∎∎∎",
    "□∎∎∎∎",
    "□□∎∎∎",
    "□□□∎∎",
    "□□□□∎",
    "□□□□□"
]

# Temp Paths
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Bot
app = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user's image paths and message IDs temporarily
user_data = {}

async def loading_animation(message):
    """Display rotating hourglass animation while processing"""
    frame_index = 0
    while True:
        try:
            await message.edit_text(f"{LOADING_FRAMES[frame_index]} Processing...")
            frame_index = (frame_index + 1) % len(LOADING_FRAMES)
            await asyncio.sleep(0.8)
        except:
            break

async def fade_out_message(message, original_text):
    """Apply fade-out effect to a message"""
    for frame in FADE_FRAMES:
        try:
            await message.edit_text(frame.format(text=original_text))
            await asyncio.sleep(0.7)
        except:
            break

async def delete_animation(message):
    """Show deletion animation for a message"""
    for frame in DELETE_ANIMATIONS:
        try:
            await message.edit_text(frame)
            await asyncio.sleep(0.5)
        except:
            break

async def delete_messages_with_effects(client, chat_id, messages_info):
    """Delete messages with fade-out and animation effects"""
    for msg_id, msg_text in messages_info:
        try:
            message = await client.get_messages(chat_id, msg_id)
            if message:
                if msg_text:  # Apply fade effect for text messages
                    await fade_out_message(message, msg_text)
                await delete_animation(message)
                await asyncio.sleep(1.0)
                await message.delete()
        except:
            pass
        await asyncio.sleep(0.8)

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("Welcome! Send me an image, and I'll let you choose which sticker to apply!")

@app.on_message(filters.photo)
async def handle_image(client, message: Message):
    try:
        # Download the image sent by the user
        photo_path = await message.download(file_name=f"{TEMP_DIR}/image_{message.chat.id}.png")
        
        # Create inline keyboard with sticker options
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("PK Sticker", callback_data="sticker_pk"),
                InlineKeyboardButton("A14 Sticker", callback_data="sticker_a14")
            ]
        ])

        # Send choice message and store relevant message IDs and image path
        choice_msg = await message.reply(
            "Choose which sticker you want to apply:",
            reply_markup=keyboard
        )
        
        user_data[message.chat.id] = {
            'image_path': photo_path,
            'messages_info': [
                (message.id, None),  # None for photo message
                (choice_msg.id, "Choose which sticker you want to apply:")
            ]
        }
        
    except Exception as e:
        await message.reply("Sorry, there was an error processing your image. Please try again.")
        if message.chat.id in user_data:
            del user_data[message.chat.id]

@app.on_callback_query()
async def handle_sticker_choice(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    
    # Check if user has data stored
    if chat_id not in user_data:
        await callback_query.answer("Please send an image first!", show_alert=True)
        return

    # Answer the callback query immediately to prevent the "loading" state
    await callback_query.answer()

    # Get the stored data
    user_info = user_data[chat_id]
    photo_path = user_info['image_path']
    
    # Determine which sticker and size to use
    if callback_query.data == "sticker_pk":
        sticker_id = PK_STICKER_ID
        sticker_size = PK_STICKER_SIZE
    else:
        sticker_id = A14_STICKER_ID
        sticker_size = A14_STICKER_SIZE
    
    try:
        # Show initial processing message without keyboard
        await callback_query.message.edit_text("⌛ Processing...", reply_markup=None)
        
        # Start loading animation in background
        animation_task = asyncio.create_task(loading_animation(callback_query.message))
        
        # Process the image in background
        async def process_image():
            # Download and process the sticker
            sticker_file = await client.download_media(sticker_id, file_name=f"{TEMP_DIR}/sticker_{chat_id}.png")
            user_image = Image.open(photo_path).convert("RGBA")
            sticker = Image.open(sticker_file).convert("RGBA")
            sticker = sticker.resize(sticker_size, Image.LANCZOS)

            # Calculate position and apply sticker
            center_x = (user_image.width - sticker.width) // 2
            center_y = (user_image.height - sticker.height) // 2
            user_image.paste(sticker, (center_x, center_y), sticker)

            # Save the modified image
            output_path = f"{TEMP_DIR}/output_{chat_id}.png"
            user_image.save(output_path)
            return sticker_file, output_path

        # Process image and clean up messages concurrently
        processing_task = asyncio.create_task(process_image())
        cleanup_task = asyncio.create_task(
            delete_messages_with_effects(client, chat_id, user_info['messages_info'][:-1])
        )
        
        # Wait for both tasks to complete
        sticker_file, output_path = await processing_task
        await cleanup_task
        
        # Cancel loading animation and delete processing message
        animation_task.cancel()
        await delete_messages_with_effects(
            client, 
            chat_id, 
            [(callback_query.message.id, "⌛ Processing...")]
        )
        
        # Send the final image
        await client.send_photo(chat_id, output_path)

        # Clean up temporary files
        os.remove(photo_path)
        os.remove(sticker_file)
        os.remove(output_path)
        del user_data[chat_id]

    except Exception as e:
        # Cancel tasks and show error
        animation_task.cancel()
        await callback_query.message.edit_text("Sorry, there was an error. Please try again.")
        
        # Clean up if there was an error
        if chat_id in user_data:
            if os.path.exists(photo_path):
                os.remove(photo_path)
            del user_data[chat_id]

if __name__ == "__main__":
    app.run()