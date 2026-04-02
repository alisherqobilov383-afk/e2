import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8680476167:AAE0eo9nPoF6w0VUeYj0ipV3eSPAVxpG6T4" # Yangi token qo'yishni unutmang!
ADMIN_ID = 8422041084 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchi holatini tozalash
    context.user_data['waiting_for_complaint'] = False
    
    # Tugmalarni yaratish (Aniq massiv ko'rinishida)
    keyboard = [
        [KeyboardButton("📝 Murojaat yozish")],
        [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]
    ]
    
    # Tugmalar paneli sozlamalari
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=False,
        input_field_placeholder="Tugmalardan birini tanlang"
    )
    
    await update.message.reply_text(
        "Assalomu alaykum! Botimizga xush kelibsiz.\n\nMurojaat qoldirish uchun quyidagi tugmalardan birini tanlang:",
        reply_markup=reply_markup
    )

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # 1. Agar foydalanuvchi tugmani bossa
    if text == "📝 Murojaat yozish":
        context.user_data['waiting_for_complaint'] = True
        await update.message.reply_text("Murojaatingizni (matn, rasm yoki video) yuboring:")
        return

    # 2. Agar murojaat kutish rejimi yoqilgan bo'lsa (Murojaat yuborish)
    if context.user_data.get('waiting_for_complaint'):
        # Adminga forward qilish
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga ID-ni yuborish (Reply qilish uchun qulay formatda)
        info_text = (
            f"📩 **YANGI MUROJAAT**\n\n"
            f"👤 Ism: {user.full_name}\n"
            f"🆔 ID: `{user.id}`\n\n"
            f"Javob berish uchun BU XABARGA 'reply' qilib yozing."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode='Markdown')
        
        await update.message.reply_text("Rahmat! Murojaatingiz adminga yetkazildi.")
        context.user_data['waiting_for_complaint'] = False
        return

    # 3. Shunchaki yozgan bo'lsa
    if not context.user_data.get('waiting_for_complaint'):
        await update.message.reply_text("Iltimos, avval '📝 Murojaat yozish' tugmasini bosing.")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 **YANGI KONTAKT**\n\nIsm: {contact.first_name}\nTel: +{contact.phone_number}\nID: `{contact.user_id}`",
        parse_mode='Markdown'
    )
    await update.message.reply_text("Kontaktingiz qabul qilindi, rahmat!")

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Faqat admin uchun va reply qilinganda ishlaydi
    if update.effective_user.id == ADMIN_ID and update.message.reply_to_message:
        try:
            msg_text = update.message.reply_to_message.text
            # ID raqamini xabar ichidan qidirish
            if "🆔 ID:" in msg_text:
                target_id = int(msg_text.split("🆔 ID:")[1].split("\n")[0].strip())
                answer = update.message.text.replace("/reply", "").strip()
                
                if answer:
                    await context.bot.send_message(chat_id=target_id, text=f"Admin javobi:\n\n{answer}")
                    await update.message.reply_text("✅ Javob yuborildi.")
                else:
                    await update.message.reply_text("⚠️ Xato: Javob matnini yozing.")
            else:
                await update.message.reply_text("❌ ID topilmadi. Ma'lumot xabariga reply qiling.")
        except Exception as e:
            logging.error(f"Reply error: {e}")
            await update.message.reply_text("❌ Xato: Foydalanuvchi ID-sini aniqlab bo'lmadi.")

# --- FLASK SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot Online!"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY QISM ---
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlerlarni tartib bilan qo'shamiz
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Barcha turdagi xabarlarni (matn, rasm, video) qabul qilish
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))
    
    app.run_polling()
