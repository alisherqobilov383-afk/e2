import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8680476167:AAE0eo9nPoF6w0VUeYj0ipV3eSPAVxpG6T4" # Tokenni yangilashni unutmang!
ADMIN_ID = 8422041084 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tugmalarni alohida-alohida qatorga qo'yamiz
    keyboard = [
        [KeyboardButton("📝 Murojaat yozish")],
        [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]
    ]
    await update.message.reply_text(
        "Assalomu alaykum! Quyidagi tugmalardan birini tanlang:", 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # 1. Tugma bosilganda holatni o'zgartirish
    if text == "📝 Murojaat yozish":
        await update.message.reply_text("Murojaatingizni yozing yoki fayl yuboring...")
        context.user_data['waiting_for_complaint'] = True
        return

    # 2. Agar foydalanuvchi murojaat yuborayotgan bo'lsa
    if context.user_data.get('waiting_for_complaint'):
        # Adminga forward qilish
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga ID-ni matn ko'rinishida yuborish (Reply qilish oson bo'lishi uchun)
        info_text = (
            f"📩 YANGI MUROJAAT\n"
            f"👤 Ism: {user.full_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔗 Username: @{user.username if user.username else 'yoq'}\n\n"
            f"Javob berish uchun BU XABARGA 'reply' qilib yozing."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode='Markdown')
        
        await update.message.reply_text("Rahmat! Murojaatingiz adminga yetkazildi.")
        context.user_data['waiting_for_complaint'] = False

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Faqat admin reply qilganda ishlaydi
    if update.effective_user.id == ADMIN_ID and update.message.reply_to_message:
        try:
            # Reply qilingan xabar matnidan ID ni qidirish
            reply_msg_text = update.message.reply_to_message.text
            
            # Matndan ID raqamini ajratib olish mantiqi
            if "🆔 ID:" in reply_msg_text:
                target_user_id = int(reply_msg_text.split("🆔 ID:")[1].split("\n")[0].strip())
                
                # /reply so'zini olib tashlab, faqat javobni qoldirish
                admin_answer = update.message.text
                if admin_answer.startswith('/reply'):
                    admin_answer = admin_answer.replace('/reply', '').strip()

                if admin_answer:
                    await context.bot.send_message(chat_id=target_user_id, text=f"Admin javobi:\n\n{admin_answer}")
                    await update.message.reply_text("✅ Javob yuborildi.")
                else:
                    await update.message.reply_text("⚠️ Xato: Javob matnini yozing (Masalan: /reply Salom).")
            else:
                await update.message.reply_text("❌ Bu xabarga javob berib bo'lmaydi. Faqat ID yozilgan xabarga reply qiling.")
        
        except Exception as e:
            logging.error(f"Reply error: {e}")
            await update.message.reply_text("❌ Xato: Foydalanuvchi ID-sini aniqlab bo'lmadi.")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    # Adminga kontaktni yuborish
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 KONTAKT KELDI:\n👤 Ism: {contact.first_name}\n☎️ Tel: +{contact.phone_number}\n🆔 ID: `{contact.user_id}`",
        parse_mode='Markdown'
    )
    await update.message.reply_text("Kontaktingiz qabul qilindi!", reply_markup=ReplyKeyboardRemove())

# --- FLASK SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot online!"

def run_web(): app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY QISM ---
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    # Kontakt kelganda handle_contact ishlaydi
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    # Boshqa xabarlar uchun handle_message
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # Rasm yoki videolar kelsa ham handle_message ishlashi uchun
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, handle_message))
    
    app.run_polling()
