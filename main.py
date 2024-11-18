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

# Different sizes for each sticker
PK_STICKER_SIZE = (300, 160)  # Width, Height for PK sticker
A14_STICKER_SIZE = (220, 160)  # Width, Height for A14 sticker

# Temp Paths
TEMP_DIR = "temp_files"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Bot
espada = Client("sticker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user's image paths and message IDs temporarily
user_data = {}

def photo_filter(_, __, message):
    """
    Enhanced filter that checks for photos in messages, including those from bots
    Returns True if the message contains a photo and meets specific criteria
    """
    # Check if message has photo
    has_photo = bool(message.photo)
    
    if not has_photo:
        return False
        
    # Handle photos from TierHarribelBot
    if message.from_user and message.from_user.is_bot:
        if message.from_user.username == "TierHarribelBot":
            return True
            
    # Handle forwarded messages from TierHarribelBot
    if message.forward_from:
        if message.forward_from.username == "TierHarribelBot":
            return True
            
    # Handle normal user photos
    if message.from_user and not message.from_user.is_bot:
        return True
        
    return False


photo_handler = filters.create(photo_filter)

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
        parse_mode = ParseMode.HTML
    )

@espada.on_message(photo_handler)
async def handle_image(client, message: Message):
    try:
        # Log detailed message information for debugging
        sender_info = {
            "user_id": message.from_user.id if message.from_user else None,
            "username": message.from_user.username if message.from_user else None,
            "is_bot": message.from_user.is_bot if message.from_user else None,
            "forward_from": message.forward_from.username if message.forward_from else None,
            "has_photo": bool(message.photo)
        }
        print(f"Processing message: {sender_info}")
        
        # Download the photo
        photo_path = await message.download(file_name=f"{TEMP_DIR}/image_{message.chat.id}.png")
        
        # Create keyboard for sticker selection
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("PK Sticker", callback_data="sticker_pk"),
                InlineKeyboardButton("A14 Sticker", callback_data="sticker_a14")
            ]
        ])

        # Send sticker selection message
        choice_msg = await message.reply(
            "Choose which sticker you want to apply:",
            reply_markup=keyboard
        )
        
        # Store message information for cleanup
        user_data[message.chat.id] = {
            'image_path': photo_path,
            'messages_info': [
                (message.id, None),
                (choice_msg.id, "Choose which sticker you want to apply:")
            ]
        }
        
    except Exception as e:
        print(f"Error in handle_image: {str(e)}")
        await message.reply("Sorry, there was an error processing your image. Please try again.")
        # Cleanup on error
        if message.chat.id in user_data:
            try:
                if 'image_path' in user_data[message.chat.id]:
                    if os.path.exists(user_data[message.chat.id]['image_path']):
                        os.remove(user_data[message.chat.id]['image_path'])
            except Exception as cleanup_error:
                print(f"Cleanup error: {str(cleanup_error)}")
            del user_data[message.chat.id]

@espada.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    current_caption = callback_query.message.caption  # Get the current caption

    if data == "home" and current_caption != HOME_TEXT:
        await callback_query.edit_message_caption(
            caption=HOME_TEXT,
            reply_markup=callback_query.message.reply_markup,
            parse_mode = ParseMode.HTML
        )
    elif data == "about" and current_caption != ABOUT_TEXT:
        await callback_query.edit_message_caption(
            caption=ABOUT_TEXT,
            reply_markup=callback_query.message.reply_markup,
            parse_mode = ParseMode.HTML
        )
    elif data == "help" and current_caption != HELP_TEXT:
        await callback_query.edit_message_caption(
            caption=HELP_TEXT,
            reply_markup=callback_query.message.reply_markup,
            parse_mode = ParseMode.HTML
        )
    elif data == "support" and current_caption != SUPPORT_TEXT:
        await callback_query.edit_message_caption(
            caption=SUPPORT_TEXT,
            reply_markup=callback_query.message.reply_markup,
            parse_mode = ParseMode.HTML
        )
    elif data in ["sticker_pk", "sticker_a14"]:
        chat_id = callback_query.message.chat.id
        
        # Check if user has data stored
        if chat_id not in user_data:
            await callback_query.answer("Please send an image first!", show_alert=True)
            return

        # Get the stored data
        user_info = user_data[chat_id]
        photo_path = user_info['image_path']
        
        # Determine which sticker and size to use
        sticker_id = PK_STICKER_ID if data == "sticker_pk" else A14_STICKER_ID
        sticker_size = PK_STICKER_SIZE if data == "sticker_pk" else A14_STICKER_SIZE
        
        try:
            # Show initial processing message without keyboard
            await callback_query.message.edit_text("⌛ Processing...", reply_markup=None)
            
            # Start loading animation
            animation_task = asyncio.create_task(loading_animation(callback_query.message))
            
            # Process image
            async def process_image():
                sticker_file = await client.download_media(sticker_id, file_name=f"{TEMP_DIR}/sticker_{chat_id}.png")
                user_image = Image.open(photo_path).convert("RGBA")
                sticker = Image.open(sticker_file).convert("RGBA")
                sticker = sticker.resize(sticker_size, Image.LANCZOS)

                center_x = (user_image.width - sticker.width) // 2
                center_y = (user_image.height - sticker.height) // 2
                user_image.paste(sticker, (center_x, center_y), sticker)

                output_path = f"{TEMP_DIR}/output_{chat_id}.png"
                user_image.save(output_path)
                return sticker_file, output_path

            # Process image and clean up messages
            processing_task = asyncio.create_task(process_image())
            cleanup_task = asyncio.create_task(
                delete_messages_with_effects(client, chat_id, user_info['messages_info'][:-1])
            )
            
            sticker_file, output_path = await processing_task
            await cleanup_task
            
            # Cancel animation and delete processing message
            animation_task.cancel()
            await delete_messages_with_effects(
                client, 
                chat_id, 
                [(callback_query.message.id, "⌛ Processing...")]
            )
            
            # Send final image
            await client.send_photo(chat_id, output_path)

            # Cleanup
            os.remove(photo_path)
            os.remove(sticker_file)
            os.remove(output_path)
            del user_data[chat_id]

        except Exception as e:
            animation_task.cancel()
            await callback_query.message.edit_text("Sorry, there was an error. Please try again.")
            
            if chat_id in user_data:
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                del user_data[chat_id]
    
    # Answer callback query
    await callback_query.answer()

if __name__ == "__main__":
    espada.run()