import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8680476167:AAE0eo9nPoF6w0VUeYj0ipV3eSPAVxpG6T4" # Tokenni yangilashni unutmang!
ADMIN_ID = 8422041084 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchi ma'lumotlarini tozalaymiz (start bosilganda)
    context.user_data['waiting_for_complaint'] = False
    
    keyboard = [
        [KeyboardButton("📝 Murojaat yozish")],
        [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]
    ]
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat qoldirish uchun tugmani bosing.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # 1. Tugma bosilganda
    if text == "📝 Murojaat yozish":
        context.user_data['waiting_for_complaint'] = True
        await update.message.reply_text("Murojaatingizni (matn, rasm yoki video) yuboring:")
        return

    # 2. Agar murojaat kutish rejimi yoqilgan bo'lsa
    if context.user_data.get('waiting_for_complaint'):
        # Adminga forward qilish (xabarning o'zini)
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga javob berish uchun ID-ni yuborish
        info_text = f"📩 YANGI MUROJAAT\n👤 Ism: {user.full_name}\n🆔 ID: `{user.id}`\n\nJavob berish uchun BU XABARGA 'reply' qiling."
        await context.bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode='Markdown')
        
        await update.message.reply_text("Murojaatingiz adminga yetkazildi. Rahmat!")
        # Murojaat qabul qilingach, kutish rejimini o'chiramiz
        context.user_data['waiting_for_complaint'] = False
        return

    # 3. Agar foydalanuvchi shunchaki nimanidir yozsa (tugmani bosmasdan)
    if not context.user_data.get('waiting_for_complaint'):
        await update.message.reply_text("Iltimos, avval '📝 Murojaat yozish' tugmasini bosing.")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 KONTAKT:\nIsm: {contact.first_name}\nTel: +{contact.phone_number}\nID: `{contact.user_id}`",
        parse_mode='Markdown'
    )
    await update.message.reply_text("Kontaktingiz qabul qilindi!")

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and update.message.reply_to_message:
        try:
            reply_msg = update.message.reply_to_message.text
            if "🆔 ID:" in reply_msg:
                user_id = int(reply_msg.split("🆔 ID:")[1].split("\n")[0].strip())
                answer = update.message.text.replace("/reply", "").strip()
                
                if answer:
                    await context.bot.send_message(chat_id=user_id, text=f"Admin javobi:\n\n{answer}")
                    await update.message.reply_text("✅ Javob yuborildi.")
                else:
                    await update.message.reply_text("⚠️ Javob matnini yozing.")
            else:
                await update.message.reply_text("❌ ID topilmadi. Ma'lumot xabariga reply qiling.")
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")

# --- FLASK SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot Ishlamoqda!"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY QISM ---
if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Bu handler rasm, video va matnlarni barchasini handle_all_messages ga yuboradi
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_messages))
    
    app.run_polling()
