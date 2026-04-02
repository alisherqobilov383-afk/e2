import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8524179314:AAG6qq-9DlczUHDRQkpyL2ZuV925wzyaMmw"
ADMIN_ID = 6123752979  # O'zingizning ID raqamingizni tekshirib ko'ring

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

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # 1. Murojaat yozishni boshlash
    if text == "📝 Murojaat yozish":
        context.user_data['waiting_for_complaint'] = True
        await update.message.reply_text(
            "Murojaatingizni yuboring (matn, rasm yoki video):",
            reply_markup=ReplyKeyboardRemove() # Tugmani vaqtincha olib tashlaymiz
        )
        return

 # 2. Murojaatni qabul qilish va Adminga yuborish
    if context.user_data.get('waiting_for_complaint'):
        # Adminga xabarni forward qilish (Matn, rasm, video hammasi o'tadi)
        try:
            await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
            
            info_text = (
                f"📩 **YANGI MUROJAAT**\n\n"
                f"👤 Ism: {user.full_name}\n"
                f"🆔 ID: `{user.id}`\n"
                f"Javob berish uchun ushbu xabarga 'reply' qiling."
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode='Markdown')
            
            # Murojaatdan keyin AVTOMATIK kontakt so'rash
            contact_keyboard = [[KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]]
            contact_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            # SIZ XOHLAGAN MATN:
            await update.message.reply_text(
                "Admin siz bilan bog'lanishi uchun raqamingizni qoldiring:",
                reply_markup=contact_markup
            )
            
            context.user_data['waiting_for_complaint'] = False
        except Exception as e:
            logging.error(f"Xatolik: {e}")
            await update.message.reply_text("Xatolik yuz berdi, iltimos qaytadan urinib ko'ring.")
        return

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    
    # Adminga kontaktni yuborish
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 **FOYDALANUVCHI KONTAKTI**\n\nIsm: {contact.first_name}\nTel: +{contact.phone_number}\nID: `{contact.user_id}`",
        parse_mode='Markdown'
    )
    
    # Asosiy menyuga qaytarish
    keyboard = [[KeyboardButton("📝 Murojaat yozish")]]
    await update.message.reply_text(
        "Kontaktingiz yuborildi. Tez orada javob beramiz!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and update.message.reply_to_message:
        try:
            # Forward qilingan xabardan yoki info xabardan ID ni olish
            msg = update.message.reply_to_message
            target_id = None
            
            if msg.forward_from:
                target_id = msg.forward_from.id
            elif "🆔 ID:" in (msg.text or ""):
                target_id = int(msg.text.split("🆔 ID:")[1].split("\n")[0].strip())

            if target_id:
                await context.bot.send_message(chat_id=target_id, text=f"Admin javobi:\n\n{update.message.text}")
                await update.message.reply_text("✅ Javob foydalanuvchiga yuborildi.")
            else:
                await update.message.reply_text("❌ Foydalanuvchi ID sini aniqlab bo'lmadi.")
        except Exception as e:
            logging.error(f"Reply error: {e}")

# --- FLASK SERVER (Render uchun) ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot ishlayapti!"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY QISM ---
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Admin javob berishi uchun (xabarga reply qilganda)
    app.add_handler(MessageHandler(filters.REPLY & filters.User(user_id=ADMIN_ID), reply_to_user))
    
    # Barcha xabarlarni handle_messages ga yuboramiz
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.CONTACT, handle_messages))
    
    print("Bot ishga tushdi...")
    app.run_polling()
