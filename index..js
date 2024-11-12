const { Telegraf } = require('telegraf');
require('dotenv').config();

const bot = new Telegraf(process.env.BOT_TOKEN);

bot.on('sticker', (ctx) => {
  const stickerId = ctx.message.sticker.file_id;
  ctx.reply(`Sticker ID: ${stickerId}`);
});

bot.launch();
console.log('Bot started. Send a sticker to get the sticker ID.');