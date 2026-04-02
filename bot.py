import logging
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8680476167:AAE0eo9nPoF6w0VUeYj0ipV3eSPAVxpG6T4"
ADMIN_ID = 8422041084  

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Murojaat yozish")],
        [KeyboardButton("📱 Kontaktni ulashish", request_contact=True)] # Kontakt so'rash tugmasi
    ]
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat qoldirish uchun tugmani bosing yoki kontaktingizni yuboring.", 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "Murojaat yozish":
        await update.message.reply_text("Murojaatingizni yozing, rasm, audio yoki videoni isbot uchun jo'nating.")
        context.user_data['waiting_for_complaint'] = True
    
    elif context.user_data.get('waiting_for_complaint'):
        # Adminga xabarni forward qilish
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga ID bilan birga xabar yuborish (Skritiy akkaunt bo'lsa ham ID ni saqlab qolish uchun)
        # Bu xabarga reply qilib javob yozasiz
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"🆔 USER_ID: `{user.id}`\n👤 Ism: {user.full_name}\n🔗 Username: @{user.username}\n\n👆 Yuqoridagi xabarga /reply buyrug'i bilan javob bering."
        )
        await update.message.reply_text("Murojaatingiz adminga yuborildi.")
        context.user_data['waiting_for_complaint'] = False

# Kontakt kelganda ishlaydigan funksiya
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 YANGI KONTAKT:\nIsm: {contact.first_name}\nTel: {contact.phone_number}\nID: {contact.user_id}"
    )
    await update.message.reply_text("Kontaktingiz qabul qilindi, rahmat!", reply_markup=ReplyKeyboardRemove())

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        # Xabarni tekshirish
        if not update.message.reply_to_message:
            await update.message.reply_text("Xatoni tuzatish: Javob berish uchun foydalanuvchi ma'lumotlari yozilgan xabarga 'reply' qiling.")
            return

        try:
            # Ma'lumotlar xabaridan ID ni qidirib topish (Regex ishlatish ham mumkin, lekin oddiyroq usul:)
            reply_msg = update.message.reply_to_message.text
            if "USER_ID:" in reply_msg:
                user_id = int(reply_msg.split("USER_ID:")[1].split("\n")[0].strip())
            else:
                # Agar forward qilingan xabarning o'ziga reply qilinsa (akkaunt ochiq bo'lsa)
                user_id = update.message.reply_to_message.forward_from.id

            reply_text = update.message.text.replace("/reply", "").strip()
            
            if reply_text:
                await context.bot.send_message(chat_id=user_id, text=f"Admin javobi:\n{reply_text}")
                await update.message.reply_text("✅ Javob yuborildi.")
            else:
                await update.message.reply_text("⚠️ Javob matnini yozing.")
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: Foydalanuvchi ID-sini aniqlab bo'lmadi. (Akkaunt yopiq bo'lishi mumkin)")

# --- FLASK SERVER ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot ishlamoqda!"

def run_web(): app_server.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    # Kontaktlarni tutib olish uchun handler
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    app.run_polling()
