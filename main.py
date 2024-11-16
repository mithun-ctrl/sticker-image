from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import tgcrypto
from pyrogram.enums import ParseMode
from PIL import Image
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import io
import asyncio
import time
from script import DELETE_ANIMATIONS, LOADING_FRAMES, FADE_FRAMES, START_IMAGE, HELP_TEXT, HOME_TEXT, ABOUT_TEXT, SUPPORT_TEXT
load_dotenv()

# Bot Config
API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
PK_STICKER_ID = os.getenv("pk_sticker_id")
A14_STICKER_ID = os.getenv("a14_sticker_id")
POST_BOT_USERNAME = os.getenv("post_bot")

# Different sizes for each sticker
PK_STICKER_SIZE = (300, 160)  # Width, Height for PK sticker
A14_STICKER_SIZE = (300, 250)  # Width, Height for A14 sticker

# Temp Paths
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Bot
espada = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user's image paths and message IDs temporarily
user_data = {}

async def loading_animation(message):
    """Display rotating hourglass animation while processing"""
    frame_index = 0
    last_content = None
    while True:
        try:
            new_content = f"{LOADING_FRAMES[frame_index]} Processing..."
            if new_content != last_content:  # Only update if content has changed
                await message.edit_text(new_content)
                last_content = new_content
            
            frame_index = (frame_index + 1) % len(LOADING_FRAMES)
            await asyncio.sleep(0.8)
        except:
            break

async def fade_out_message(message, original_text):
    """Apply fade-out effect to a message"""
    last_content = None  # Track the last content
    
    for frame in FADE_FRAMES:
        try:
            new_content = frame.format(text=original_text)
            if new_content != last_content:  # Only update if content has changed
                await message.edit_text(new_content)
                last_content = new_content
            await asyncio.sleep(0.7)
        except:
            break

async def delete_animation(message):
    """Show deletion animation for a message"""
    last_content = None  # Track the last content

    for frame in DELETE_ANIMATIONS:
        try:
            if frame != last_content:  # Only update if content has changed
                await message.edit_text(frame)
                last_content = frame
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
        
async def process_image_with_sticker(client, chat_id, sticker_type):
    """Process image with selected sticker"""
    try:
        # Get the stored data
        user_info = user_data[chat_id]
        photo_path = user_info['image_path']
        
        # Determine which sticker and size to use
        sticker_id = PK_STICKER_ID if sticker_type == "sticker_pk" else A14_STICKER_ID
        sticker_size = PK_STICKER_SIZE if sticker_type == "sticker_pk" else A14_STICKER_SIZE
        
        # Process image
        sticker_file = await client.download_media(sticker_id, file_name=f"{TEMP_DIR}/sticker_{chat_id}.png")
        user_image = Image.open(photo_path).convert("RGBA")
        sticker = Image.open(sticker_file).convert("RGBA")
        sticker = sticker.resize(sticker_size, Image.LANCZOS)

        center_x = (user_image.width - sticker.width) // 2
        center_y = (user_image.height - sticker.height) // 2
        user_image.paste(sticker, (center_x, center_y), sticker)

        output_path = f"{TEMP_DIR}/output_{chat_id}.png"
        user_image.save(output_path)
        
        # Send final image
        await client.send_photo(chat_id, output_path)

        # Cleanup
        os.remove(photo_path)
        os.remove(sticker_file)
        os.remove(output_path)
        del user_data[chat_id]

    except Exception as e:
        if chat_id in user_data:
            if os.path.exists(photo_path):
                os.remove(photo_path)
            del user_data[chat_id]
        raise e

@espada.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Home", callback_data="home"),
        InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("📞 Support", callback_data="support"),
        InlineKeyboardButton("❓ Help", callback_data="help")]
    ])

    await client.send_photo(
        chat_id=message.chat.id,
        photo=START_IMAGE,
        caption=HOME_TEXT,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@espada.on_message(filters.photo | filters.forwarded)
async def handle_image(client, message: Message):
    try:
        # Check if the message contains a photo (either direct or forwarded)
        if message.photo or (message.forward_from and hasattr(message, 'photo')):
            photo_path = await message.download(file_name=f"{TEMP_DIR}/image_{message.chat.id}.png")
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("PK Sticker", callback_data="sticker_pk"),
                    InlineKeyboardButton("A14 Sticker", callback_data="sticker_a14")
                ]
            ])

            # Check if it's from your specific bot
            is_from_imager_bot = (
                message.forward_from and 
                message.forward_from.is_bot and 
                message.forward_from.username == POST_BOT_USERNAME
            )

            if is_from_imager_bot:
                # Automatically apply a default sticker for images from IMager_Sender
                user_data[message.chat.id] = {
                    'image_path': photo_path,
                    'messages_info': [(message.id, None)]
                }
                await process_image_with_sticker(client, message.chat.id, "sticker_pk")
            else:
                # For other images, show the sticker selection keyboard
                choice_msg = await message.reply(
                    "Choose which sticker you want to apply:",
                    reply_markup=keyboard
                )
                
                user_data[message.chat.id] = {
                    'image_path': photo_path,
                    'messages_info': [
                        (message.id, None),
                        (choice_msg.id, "Choose which sticker you want to apply:")
                    ]
                }
        
    except Exception as e:
        await message.reply("Sorry, there was an error processing your image. Please try again.")
        if message.chat.id in user_data:
            photo_path = user_data[message.chat.id].get('image_path')
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
            del user_data[message.chat.id]
            

@espada.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    current_caption = callback_query.message.caption

    try:
        if data in ["sticker_pk", "sticker_a14"]:
            chat_id = callback_query.message.chat.id
            
            if chat_id not in user_data:
                await callback_query.answer("Please send an image first!", show_alert=True)
                return

            # Show initial processing message without keyboard
            processing_msg = await callback_query.message.edit_text("⌛ Processing...", reply_markup=None)
            
            # Start loading animation
            animation_task = asyncio.create_task(loading_animation(processing_msg))
            
            try:
                # Process image and clean up messages
                await process_image_with_sticker(client, chat_id, data)
                await delete_messages_with_effects(client, chat_id, user_data[chat_id]['messages_info'])
            finally:
                # Cancel animation and delete processing message
                animation_task.cancel()
                await delete_messages_with_effects(
                    client, 
                    chat_id, 
                    [(processing_msg.id, "⌛ Processing...")]
                )

        elif data in ["home", "about", "help", "support"]:
            caption_map = {
                "home": HOME_TEXT,
                "about": ABOUT_TEXT,
                "help": HELP_TEXT,
                "support": SUPPORT_TEXT
            }
            
            if current_caption != caption_map[data]:
                await callback_query.edit_message_caption(
                    caption=caption_map[data],
                    reply_markup=callback_query.message.reply_markup,
                    parse_mode=ParseMode.HTML
                )

        # Answer callback query
        await callback_query.answer()

    except Exception as e:
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        if callback_query.message.chat.id in user_data:
            del user_data[callback_query.message.chat.id]

if __name__ == "__main__":
    espada.run()