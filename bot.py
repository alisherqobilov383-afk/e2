import logging
import threading
import re
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8524179314:AAG6qq-9DlczUHDRQkpyL2ZuV925wzyaMmw"
ADMIN_ID = 6123752979  # O'zingizning ID raqamingizni yozing

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni boshlash"""
    context.user_data['chat_active'] = False
    keyboard = [[KeyboardButton("📝 Murojaat yozish")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat qoldirish uchun tugmani bosing:",
        reply_markup=reply_markup
    )

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin reply qilganda foydalanuvchiga yuborish"""
    if not update.message.reply_to_message:
        return

    target_id = None
    reply_msg = update.message.reply_to_message

    # Admin yuborgan info xabardan ID ni qidirish
    if reply_msg.text:
        match = re.search(r"ID:\s*(\d+)", reply_msg.text)
        if match:
            target_id = int(match.group(1))

    # Agar topilmasa, forward qilingan xabardan olish
    if not target_id and reply_msg.forward_from:
        target_id = reply_msg.forward_from.id

    if target_id:
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"👨‍💻 Admin javobi:\n\n{update.message.text}"
            )
            await update.message.reply_text("✅ Javob yuborildi.")
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")

async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi xabarlarini adminga avtomatik yuborish"""
    user = update.effective_user
    text = update.message.text

    # Tugma bosilganda chatni faollashtirish
    if text == "📝 Murojaat yozish":
        context.user_data['chat_active'] = True
        contact_btn = [[KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]]
        markup = ReplyKeyboardMarkup(contact_btn, resize_keyboard=True)
        await update.message.reply_text("Iltimos murojaatingizni batafsil yozing. (matn, rasm, video, audio):", reply_markup=markup)
        return

    # Foydalanuvchi shunchaki yozsa va chat faol bo'lsa
    if context.user_data.get('chat_active'):
        # Adminga forward qilish (Rasm/Video/Fayl hammasini olib o'tadi)
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga reply qilish uchun qulay xabar
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Yangi xabar!\n👤 {user.full_name}\n🆔 ID: {user.id}\n\n👆 Javob berish uchun tepadan xabarni o'ziga yoki shu xabarga 'Reply' qiling."
        )
        
        # Foydalanuvchiga eslatma
        await update.message.reply_text("Murojaatingiz adminga yuborildi. Admin siz bilan bog'lanishi uchun, iltimos raqamingizni qoldiring:")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kontakt kelganda"""
    contact = update.message.contact
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 KONTAKT: {contact.first_name}\nTel: +{contact.phone_number}\nID: {contact.user_id}"
    )
    await update.message.reply_text("Kontaktingiz qabul qilindi!")

# --- SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot Active"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- MAIN ---
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    # 1. Admin Reply (Eng ustuvor)
    app.add_handler(MessageHandler(filters.REPLY & filters.User(user_id=ADMIN_ID), admin_reply_handler))
    
    # 2. Kontakt
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # 3. Foydalanuvchi xabarlari (Admin bo'lmaganlar uchun)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.User(user_id=ADMIN_ID), user_message_handler))
    
    # 4. Start
    app.add_handler(CommandHandler("start", start))
    
    app.run_polling()
