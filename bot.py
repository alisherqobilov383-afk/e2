import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8524179314:AAGNsnAvlH_F_ZOz8hhpkVnYJttV34ENDTU"
ADMIN_ID = 6123752979  # Adminning ID raqami (butun son ko'rinishida)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Murojaat yozish")]]
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat qoldirish uchun tugmani bosing.", 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "Murojaat yozish":
        await update.message.reply_text("Assalomu alaykum! Murojaatingizni yozing, rasm, audio yoki videoni isbot uchun jo'nating.")
        context.user_data['waiting_for_complaint'] = True
    
    elif context.user_data.get('waiting_for_complaint'):
        # Adminga xabarni forward qilish
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        # Adminga foydalanuvchi ma'lumotlarini yuborish
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"Yuboruvchi: {user.full_name}\nUsername: @{user.username}\nID: {user.id}"
        )
        await update.message.reply_text("Murojaatingiz adminga yuborildi.")
        context.user_data['waiting_for_complaint'] = False

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin /reply buyrug'i orqali javob berishi uchun
    if update.effective_user.id == ADMIN_ID and update.message.reply_to_message:
        # Forward qilingan xabardan user_id ni aniqlash
        user_id = update.message.reply_to_message.forward_from.id
        reply_text = update.message.text.replace("/reply", "").strip()
        
        if reply_text:
            await context.bot.send_message(chat_id=user_id, text=f"Admin javobi:\n{reply_text}")
            await update.message.reply_text("Javob yuborildi.")
        else:
            await update.message.reply_text("Javob matnini yozing (masalan: /reply Salom).")

# --- FLASK SERVER (Render uchun) ---
app_server = Flask(__name__)

@app_server.route('/')
def home():
    return "Bot ishlamoqda!"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY QISM ---
if __name__ == '__main__':
    # Veb-serverni fon rejimida ishga tushiramiz
    threading.Thread(target=run_web, daemon=True).start()
    
    # Botni ishga tushirish
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    app.run_polling()
