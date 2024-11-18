# Telegram Sticker Bot 🎯

A Telegram bot that applies custom stickers to images with position customization. Built with Pyrogram and MongoDB.

## Features ✨

- Apply custom stickers to images
- Two sticker options: PK and A14
- Customizable sticker positioning
- User preference storage in MongoDB
- Simple and intuitive interface

## Prerequisites 📋

- Python 3.8 or higher
- MongoDB database
- Telegram Bot Token
- Telegram API credentials (API ID and API Hash)

## Deploy to Railway 🚂

### Quick Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/YourUsername/telegram-sticker-bot)

### Manual Deployment Steps

1. Fork this repository

2. Create a new project on [Railway](https://railway.app/)

3. Add the following environment variables in Railway:
   - `API_ID` - Your Telegram API ID
   - `API_HASH` - Your Telegram API Hash
   - `BOT_TOKEN` - Your Telegram Bot Token
   - `MONGO_URI` - Your MongoDB connection URI
   - `DB_NAME` - Database name (default: sticker_bot)

4. Connect your GitHub repository to Railway

5. Deploy! Railway will automatically detect the Procfile and start the bot

## Local Development 💻

1. Clone the repository:
```bash
git clone https://github.com/YourUsername/telegram-sticker-bot.git
cd telegram-sticker-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
MONGO_URI=your_mongodb_uri
DB_NAME=sticker_bot
```

5. Run the bot:
```bash
python main.py
```

## Usage 🎯

1. Start the bot: `/start`
2. Send an image
3. Reply to the image with `/sticker` or `/st`
4. Select sticker type (PK or A14)
5. Use `/set x y` to adjust sticker position

## Commands 📝

- `/start` - Start the bot
- `/sticker` or `/st` - Apply sticker to an image
- `/set x y` - Set sticker position (e.g., `/set 100 100`)
- `/position` - Check current sticker position

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 🆘

For support, contact [@YourTelegramUsername](https://t.me/YourTelegramUsername) on Telegram.

## Credits 🙏

- [Pyrogram](https://docs.pyrogram.org/)
- [MongoDB](https://www.mongodb.com/)
- [Python-Telegram-Bot](https://python-telegram-bot.org/)