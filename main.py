from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from config import MONGO_URI, COLLECTION_NAME, DB_NAME, STICKERS, API_HASH, API_ID, BOT_TOKEN

api_id = API_ID
api_hash = API_HASH
bot_token = BOT_TOKEN

app = Client("sticker_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Initialize MongoDB client
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
user_preferences = db[COLLECTION_NAME]

# Store temporary image paths
temp_images = {}

async def get_user_position(user_id: int) -> tuple:
    user_data = await user_preferences.find_one({"_id": user_id})
    if user_data is None:
        await set_user_position(user_id, 0, 0)
        return 0, 0
    return user_data["x_position"], user_data["y_position"]

async def set_user_position(user_id: int, x_pos: int, y_pos: int):
    await user_preferences.update_one(
        {"_id": user_id},
        {
            "$set": {
                "x_position": x_pos,
                "y_position": y_pos,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )

def apply_sticker(image_path: str, sticker_path: str, x_offset: int, y_offset: int) -> str:
    base_image = Image.open(image_path).convert('RGBA')
    sticker = Image.open(sticker_path).convert('RGBA')
    
    new_image = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
    new_image.paste(base_image, (0, 0))
    
    x_pos = x_offset
    y_pos = y_offset
    
    new_image.paste(sticker, (x_pos, y_pos), sticker)
    
    output_path = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    new_image.save(output_path)
    return output_path

def get_sticker_selection_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("PK", callback_data="sticker_pk"),
            InlineKeyboardButton("A14", callback_data="sticker_a14"),
            InlineKeyboardButton("Cancel", callback_data="cancel_sticker")
        ]
    ])

@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = (
        "Welcome to the Sticker Bot! 🎉\n\n"
        "Commands:\n"
        "📌 /sticker or /st - Apply sticker to an image\n"
        "⚙️ /set x y - Set sticker position (e.g., /set 100 100)\n"
        "❓ /position - Check your current sticker position"
    )
    await message.reply_text(welcome_text)

@app.on_message(filters.command("position"))
async def get_position_command(client, message):
    x, y = await get_user_position(message.from_user.id)
    await message.reply_text(f"Your current sticker position is x:{x}, y:{y}")

@app.on_message(filters.command("set"))
async def set_position(client, message):
    try:
        _, x, y = message.text.split()
        x, y = int(x), int(y)
        
        if x < 0 or y < 0:
            raise ValueError("Coordinates must be positive numbers")
        
        await set_user_position(message.from_user.id, x, y)
        
        await message.reply_text(
            f"✅ Sticker position set to x:{x}, y:{y}\n"
            "Send an image and reply with /sticker to test it!"
        )
    except ValueError:
        await message.reply_text(
            "❌ Please use the correct format: /set x y\n"
            "Example: /set 100 100\n"
            "Note: Coordinates must be positive numbers"
        )

@app.on_message(filters.command(["sticker", "st"]))
async def handle_sticker_command(client, message):
    if message.reply_to_message and message.reply_to_message.photo:
        # Download and store the image path temporarily
        photo_path = await message.reply_to_message.download()
        temp_images[message.from_user.id] = photo_path
        
        # Show sticker selection buttons
        await message.reply_text(
            "Please select a sticker to apply:",
            reply_markup=get_sticker_selection_keyboard()
        )
    else:
        await message.reply_text(
            "⚠️ Please reply to an image with /sticker or /st command\n"
            "Example:\n"
            "1. Send an image\n"
            "2. Reply to it with /sticker"
        )

@app.on_callback_query(filters.regex('^sticker_|^cancel_'))
async def handle_sticker_selection(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if callback_query.data == "cancel_sticker":
        # Clean up stored image
        if user_id in temp_images:
            os.remove(temp_images[user_id])
            del temp_images[user_id]
        await callback_query.message.edit_text("❌ Sticker application cancelled")
        return

    try:
        if user_id not in temp_images:
            await callback_query.answer("❌ No image found. Please try again.", show_alert=True)
            return

        # Get selected sticker
        sticker_type = callback_query.data.split('_')[1]
        sticker_file_id = STICKERS[sticker_type]

        # Show processing message
        await callback_query.message.edit_text("Processing your image... 🔄")

        # Download the sticker
        sticker_path = await client.download_media(sticker_file_id)

        # Get user's position preferences
        x_offset, y_offset = await get_user_position(user_id)

        # Apply the sticker
        output_path = apply_sticker(temp_images[user_id], sticker_path, x_offset, y_offset)

        # Send the processed image
        await callback_query.message.reply_photo(
            output_path,
            caption=f"Here's your image with the {sticker_type.upper()} sticker! 🎉"
        )

        # Clean up
        os.remove(temp_images[user_id])
        os.remove(sticker_path)
        os.remove(output_path)
        del temp_images[user_id]

        await callback_query.message.delete()

    except Exception as e:
        await callback_query.message.edit_text(f"❌ Error processing image: {str(e)}")
        if user_id in temp_images:
            os.remove(temp_images[user_id])
            del temp_images[user_id]

@app.on_message(filters.error)
async def error_handler(client, message):
    await message.reply_text(
        "❌ An error occurred while processing your request.\n"
        "Please try again later or contact support if the issue persists."
    )

if __name__ == "__main__":
    print("Bot is starting... 🚀")
    app.run()