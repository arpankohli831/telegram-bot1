import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "8701288395:AAGabCphFdZmJ6tG1A5NH5SzKAAtk0g-JjM"
bot = telebot.TeleBot(BOT_TOKEN)

def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🟢 ADD FUNDS")
    keyboard.row("🔵 FACEBOOK ₹25", "🔵 GOOGLE ₹25")
    keyboard.row("🔵 TWITTER ₹25", "🔵 GUEST ₹20")
    keyboard.row("🟡 STOCK", "🟡 MY BALANCE")
    keyboard.row("🟣 PROMO CODE", "🟣 REFER & EARN")
    keyboard.row("⭐ PAID PUSH ⭐", "🔗 CHANNEL")
    keyboard.row("⚫ CONTACT OWNER")
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to our service bot 👋\nChoose an option below:",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text

    if text == "🟢 ADD FUNDS":
        bot.reply_to(message, "💰 Send payment screenshot to admin.")

    elif text == "🟡 MY BALANCE":
        bot.reply_to(message, "💳 Your balance: ₹0")

    elif text == "🔗 CHANNEL":
        bot.reply_to(message, "📢 Join our channel:\nhttps://t.me/yourchannel")

    elif text == "⚫ CONTACT OWNER":
        bot.reply_to(message, "👤 Contact Owner:\n@yourusername")

    else:
        bot.reply_to(message, f"✅ You selected: {text}")

bot.infinity_polling()