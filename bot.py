import sqlite3
import os
import sys
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

keep_alive()

# ================= CONFIG ================= #
BOT_TOKEN = "8701288395:AAGabCphFdZmJ6tG1A5NH5SzKAAtk0g-JjM"
ADMIN_ID = 7853887140
OWNER_USERNAME = "@ARPANMODX"
UPI_ID = "7908684711@fam"
QR_IMAGE_PATH = "upi_qr.png"
REF_BONUS = 1  # ₹1 per referral

# ================= DATABASE ================= #
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referrer_id INTEGER,
    referred_count INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    data TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS promocodes (
    code TEXT PRIMARY KEY,
    amount INTEGER,
    max_uses INTEGER,
    used INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS promo_used (
    user_id INTEGER,
    code TEXT,
    UNIQUE(user_id, code)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    referrer INTEGER,
    referred INTEGER,
    UNIQUE(referrer, referred)
)
""")

conn.commit()

# ================= PRICES ================= #
PRICES = {
    "facebook": 25,
    "google": 25,
    "twitter": 25,
    "guest": 20
}

# ================= HELPERS ================= #
def add_user(uid, ref=None):
    cur.execute("SELECT 1 FROM users WHERE user_id=?", (uid,))
    if cur.fetchone():
        return
    cur.execute("INSERT INTO users VALUES (?,?,?,?)", (uid, 0, ref, 0))
    if ref and ref != uid:
        cur.execute("SELECT 1 FROM referrals WHERE referrer=? AND referred=?", (ref, uid))
        if not cur.fetchone():
            cur.execute(
                "UPDATE users SET balance=balance+?, referred_count=referred_count+1 WHERE user_id=?",
                (REF_BONUS, ref)
            )
            cur.execute("INSERT INTO referrals VALUES (?,?)", (ref, uid))
    conn.commit()

def balance(uid):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

def add_balance(uid, amt):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
    conn.commit()

def deduct(uid, amt):
    cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amt, uid))
    conn.commit()

def add_stock(t, d):
    cur.execute("INSERT INTO stock (type,data) VALUES (?,?)", (t, d))
    conn.commit()

def get_stock(t):
    cur.execute("SELECT id,data FROM stock WHERE type=? LIMIT 1", (t,))
    r = cur.fetchone()
    if not r:
        return None
    cur.execute("DELETE FROM stock WHERE id=?", (r[0],))
    conn.commit()
    return r[1]

def stock_count(t):
    cur.execute("SELECT COUNT(*) FROM stock WHERE type=?", (t,))
    return cur.fetchone()[0]

def referral_count(uid):
    cur.execute("SELECT referred_count FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()[0]

# ================= ✅ NEW SAFE QR ADDITION ================= #
async def safe_send_qr(update):
    if os.path.exists(QR_IMAGE_PATH):
        await update.message.reply_photo(
            photo=open(QR_IMAGE_PATH, "rb"),
            caption=f"💰 Scan & Pay\n\nUPI: {UPI_ID}\nSend UTR to {OWNER_USERNAME}"
        )
    else:
        await update.message.reply_text(
            f"💰 ADD FUNDS\n\nUPI ID: {UPI_ID}\nSend UTR to {OWNER_USERNAME}"
        )

# ================= KEYBOARD ================= #
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🟢 ADD FUNDS"],
            ["🔵 FACEBOOK ₹25", "🔵 GOOGLE ₹25"],
            ["🔵 TWITTER ₹25", "🔵 GUEST ₹20"],
            ["🟡 STOCK", "🟡 MY BALANCE"],
            ["🟣 PROMO CODE", "🟣 REFER & EARN"],
            ["⭐ PAID PUSH⭐", "🔗 CHANNEL"],
            ["⚫ CONTACT OWNER"]
        ],
        resize_keyboard=True
    )

awaiting_promo = set()

# ================= START ================= #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref = int(context.args[0]) if context.args and context.args[0].isdigit() else None
    add_user(uid, ref)
    await update.message.reply_text(
        "🔥 *WELCOME TO 8 LEVEL ID SELLER BOT*\n\nChoose option 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

# ================= REFER ================= #
async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/Arpan_8_level_id_sell_bot?start={uid}"
    await update.message.reply_text(
        f"👥 REFER & EARN\n\n🔗 {link}\n\nEarn ₹{REF_BONUS} per referral\nTotal Referrals: {referral_count(uid)}"
    )

# ================= MENU ================= #
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    if text == "🟡 MY BALANCE":
        await update.message.reply_text(f"💰 Balance: ₹{balance(uid)}")

    elif text == "🟡 STOCK":
        await update.message.reply_text(
            f"📦 STOCK\n\n"
            f"Facebook: {stock_count('facebook')}\n"
            f"Google: {stock_count('google')}\n"
            f"Twitter: {stock_count('twitter')}\n"
            f"Guest: {stock_count('guest')}"
        )

    elif text == "🟢 ADD FUNDS":
        await safe_send_qr(update)   # ✅ ONLY ADDITION USED HERE

    elif text in ["🔵 FACEBOOK ₹25", "🔵 GOOGLE ₹25", "🔵 TWITTER ₹25", "🔵 GUEST ₹20"]:
        t = ("facebook" if "FACEBOOK" in text else
             "google" if "GOOGLE" in text else
             "twitter" if "TWITTER" in text else
             "guest")

        if balance(uid) < PRICES[t]:
            await update.message.reply_text("❌ Not enough balance")
            return

        acc = get_stock(t)
        if not acc:
            await update.message.reply_text("❌ Out of stock")
            return

        deduct(uid, PRICES[t])
        await update.message.reply_text(
            f"✅ PURCHASED\n\n{acc}\nRemaining Balance: ₹{balance(uid)}"
        )

    elif text == "🟣 REFER & EARN":
        await refer_command(update, context)

    elif text == "🟣 PROMO CODE":
        awaiting_promo.add(uid)
        await update.message.reply_text("💌 Send your promo code now:")

    elif text == "⭐ PAID PUSH⭐":
        kb = [
            [InlineKeyboardButton("⭐ 1 STAR — ₹2", url="https://t.me/ARPANMODX")],
            [InlineKeyboardButton("⭐⭐ 10 STAR — ₹20", url="https://t.me/ARPANMODX")],
            [InlineKeyboardButton("⭐⭐⭐ 25 STAR — ₹50", url="https://t.me/ARPANMODX")]
        ]
        await update.message.reply_text(
            "⭐ PAID PUSH PRICES\n\nContact Owner: @ARPANMODX",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif text == "⚫ CONTACT OWNER":
    await update.message.reply_text(
        "👤 Contact Owner\n"
        "Username: @ARPANMODX\n"
        "🔗 https://t.me/ARPANMODX"
    )

# ================= MESSAGE HANDLER ================= #
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid in awaiting_promo:
        awaiting_promo.remove(uid)
        code = text.upper()
        cur.execute("SELECT amount, max_uses, used FROM promocodes WHERE code=?", (code,))
        row = cur.fetchone()
        if not row:
            await update.message.reply_text("❌ Invalid promo code")
            return
        amount, max_uses, used = row
        if used >= max_uses:
            await update.message.reply_text("❌ Promo expired")
            return
        cur.execute("SELECT 1 FROM promo_used WHERE user_id=? AND code=?", (uid, code))
        if cur.fetchone():
            await update.message.reply_text("❌ Already used")
            return
        add_balance(uid, amount)
        cur.execute("UPDATE promocodes SET used=used+1 WHERE code=?", (code,))
        cur.execute("INSERT INTO promo_used VALUES (?,?)", (uid, code))
        conn.commit()
        await update.message.reply_text(f"✅ Promo applied! ₹{amount} added")
        return

    await menu(update, context)

# ================= RUN ================= #
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("refer", refer_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("Bot running...")
app.run_polling()