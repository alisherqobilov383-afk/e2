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
    context.user_data['waiting_for_complaint'] = False
    keyboard = [[KeyboardButton("📝 Murojaat yozish")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat qoldirish uchun quyidagi tugmani bosing:",
        reply_markup=reply_markup
    )

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin javob berganda (REPLY)"""
    if update.effective_user.id != ADMIN_ID or not update.message.reply_to_message:
        return

    reply_msg = update.message.reply_to_message
    target_id = None

    if reply_msg.text:
        match = re.search(r"🆔 ID:\s*(\d+)", reply_msg.text)
        if match:
            target_id = int(match.group(1))

    if not target_id and reply_msg.forward_from:
        target_id = reply_msg.forward_from.id

    if target_id:
        try:
            await context.bot.send_message(chat_id=target_id, text=f"Admin javobi:\n\n{update.message.text}")
            await update.message.reply_text(f"✅ Javob yuborildi (ID: {target_id})")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # 1. Murojaat yozish tugmasi
    if text == "📝 Murojaat yozish":
        context.user_data['waiting_for_complaint'] = True
        # Kontakt tugmasini darhol chiqarib qo'yamiz, foydalanuvchi xohlasa yuboradi, xohlasa yozaveradi
        contact_keyboard = [[KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]]
        markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True)
        await update.message.reply_text("Murojaatingizni yuboring (matn, rasm yoki video):", reply_markup=markup)
        return

    # 2. Murojaat holati yoqilgan bo'lsa (Kontakt yuborguncha o'chmaydi)
    if context.user_data.get('waiting_for_complaint'):
        # Adminga forward qilish
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga info
        info_text = f"📩 **YANGI MUROJAAT**\n👤 Ism: {user.full_name}\n🆔 ID: {user.id}\nJavob berish uchun reply qiling."
        await context.bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode='Markdown')
        
        # Foydalanuvchiga eslatma (lekin holatni False qilmaymiz, yana yozishi mumkin)
        await update.message.reply_text("Admin siz bilan bog'lanishi uchun raqamingizni qoldiring (yoki murojaatni davom ettiring):")
        return
    else:
        await update.message.reply_text("Iltimos, avval '📝 Murojaat yozish' tugmasini bosing.")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    # Adminga yuborish
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 **KONTAKT**\nIsm: {contact.first_name}\nTel: +{contact.phone_number}\nID: {contact.user_id}",
        parse_mode='Markdown'
    )
    # Kontakt kelgandan keyingina murojaat rejimi yopiladi
    context.user_data['waiting_for_complaint'] = False
    
    keyboard = [[KeyboardButton("📝 Murojaat yozish")]]
    await update.message.reply_text(
        "Kontaktingiz qabul qilindi. Rahmat!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# --- FLASK SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot Online!"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY ---
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.REPLY & filters.User(user_id=ADMIN_ID), reply_to_user))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.CONTACT, handle_messages))
    
    app.run_polling()
