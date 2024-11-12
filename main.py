import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv
load_dotenv()

# Load the bot token from the environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! Send me a sticker to get its ID.")

def get_sticker_id(update, context):
    sticker = update.message.sticker
    sticker_id = sticker.file_id
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Sticker ID: {sticker_id}")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add handlers for the /start command and sticker messages
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.sticker, get_sticker_id))

    # Start the bot
    updater.start_polling()
    print('Bot started. Send a sticker to get the sticker ID.')
    updater.idle()

if __name__ == '__main__':
    main()