import logging
import threading
import re
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- SOZLAMALAR ---
TOKEN = "8524179314:AAG6qq-9DlczUHDRQkpyL2ZuV925wzyaMmw"
ADMIN_ID = 6123752979 # O'zingizning Telegram ID raqamingizni yozing

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botni boshlash"""
    context.user_data['waiting_for_complaint'] = False
    
    keyboard = [[KeyboardButton("📝 Murojaat yozish")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Assalomu alaykum! Murojaat qoldirish uchun quyidagi tugmani bosing:",
        reply_markup=reply_markup
    )

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin foydalanuvchiga javob berishi (REPLY)"""
    # Faqat admin reply qilganda va bu javob xabari bo'lganda ishlaydi
    if update.effective_user.id != ADMIN_ID or not update.message.reply_to_message:
        return

    reply_msg = update.message.reply_to_message
    target_id = None

    # 1. Matndan ID ni qidirish (Eng ishonchli yo'l)
    if reply_msg.text:
        match = re.search(r"🆔 ID:\s*(\d+)", reply_msg.text)
        if match:
            target_id = int(match.group(1))

    # 2. Agar matnda topilmasa, forward qilingan xabardan olishga urinish
    if not target_id and reply_msg.forward_from:
        target_id = reply_msg.forward_from.id

    if target_id:
        try:
            await context.bot.send_message(
                chat_id=target_id, 
                text=f"Админ жавоби:\n\n{update.message.text}"
            )
            await update.message.reply_text(f"✅ Жавоб юборилди (ID: {target_id})")
        except Exception as e:
            await update.message.reply_text(f"❌ Юборишда хатолик: {e}")
    else:
        await update.message.reply_text("❌ Фойдаланувчи ID сини аниқлаб бўлмади. Илтимос, '🆔 ID:' ёзилган хабарга жавоб беринг.")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarlarni saralash va murojaatlarni qabul qilish"""
    user = update.effective_user
    text = update.message.text

    # 1. Murojaat yozish tugmasi bosilganda
    if text == "📝 Murojaat yozish":
        context.user_data['waiting_for_complaint'] = True
        await update.message.reply_text(
            "Murojaatingizni yuboring (matn, rasm yoki video):",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # 2. Murojaat kutish holatida xabar kelsa
    if context.user_data.get('waiting_for_complaint'):
        # Adminga forward qilish
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)
        
        # Adminga info yuborish
        info_text = (
            f"📩 **YANGI MUROJAAT**\n\n"
            f"👤 Ism: {user.full_name}\n"
            f"🆔 ID: {user.id}\n"
            f"Javob berish uchun ushbu xabarga 'reply' qiling."
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=info_text, parse_mode='Markdown')
        
        # Foydalanuvchidan avtomatik kontakt so'rash
        contact_keyboard = [[KeyboardButton("📱 Kontaktni ulashish", request_contact=True)]]
        contact_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "Murojaatingiz ko'rib chiqilishi uchun adminga yuborildi. Admin siz bilan bog'lanishi uchun raqamingizni qoldiring:",
            reply_markup=contact_markup
        )
        
        context.user_data['waiting_for_complaint'] = False
        return

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kontakt kelganda"""
    contact = update.message.contact
    
    # Adminga kontaktni yuborish
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📞 **KONTAKT**\n\nIsm: {contact.first_name}\nTel: +{contact.phone_number}\nID: {contact.user_id}",
        parse_mode='Markdown'
    )
    
    # Asosiy menyu
    keyboard = [[KeyboardButton("📝 Murojaat yozish")]]
    await update.message.reply_text(
        "Kontaktingiz yuborildi. Tez orada javob beramiz!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# --- FLASK SERVER (Render/VPS uchun) ---
app_server = Flask(__name__)
@app_server.route('/')
def home(): return "Bot Online!"

def run_web():
    app_server.run(host='0.0.0.0', port=10000)

# --- ASOSIY QISM ---
if __name__ == '__main__':
    # Web serverni alohida oqimda yurgizish
    threading.Thread(target=run_web, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # HANDLERLAR TARTIBI (Reply tepada turishi shart!)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.REPLY & filters.User(user_id=ADMIN_ID), reply_to_user))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    # Qolgan barcha xabarlar (Matn, rasm, video) uchun
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))
    
    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()
