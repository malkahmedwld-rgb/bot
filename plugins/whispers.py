# plugins/whispers.py
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

# مخزن مؤقت للهمسات
# الهيكل: {uuid: {'from_id': 123, 'to_id': 456, 'text': '...', 'sender_name': 'Ali'}}
whispers_data = {}
# لتتبع من يكتب همسة حالياً في الخاص
pending_writers = {}

async def initiate_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    # التأكد أن الأمر رد على رسالة وأنها ليست لبوت
    if not msg.reply_to_message:
        await msg.reply_text("⚠️ لازم ترد على رسالة شخص عشان تهمس له!")
        return
    
    receiver = msg.reply_to_message.from_user
    sender = msg.from_user

    if receiver.is_bot:
        await msg.reply_text("🤖 ما تقدرش تهمس لبوت يا محاينك!")
        return

    # إنشاء معرف فريد للهمسة
    w_id = str(uuid.uuid4())[:8]
    
    # حفظ بيانات الهمسة المبدئية
    whispers_data[w_id] = {
        'from_id': sender.id,
        'to_id': receiver.id,
        'to_name': receiver.first_name,
        'sender_name': sender.first_name,
        'chat_id': update.effective_chat.id,
        'text': None
    }

    # رابط الانتقال للخاص (Deep Linking)
    bot_username = context.bot.username
    url = f"https://t.me/{bot_username}?start=w_{w_id}"
    
    kb = [[InlineKeyboardButton("🤫 اكتب نميمتك هنا", url=url)]]
    await msg.reply_text(
        f"يا [{sender.first_name}](tg://user?id={sender.id})، اضغط الزر تحت عشان تكتب الهمسة لـ {receiver.first_name} في السكات.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def handle_start_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق هل الرابط يحتوي على كود همسة (مثال: /start w_1234abcd)
    if not context.args or not context.args[0].startswith("w_"):
        return False # هذا يعني أنه start عادي وليس همسة
    
    w_id = context.args[0].replace("w_", "")
    if w_id in whispers_data:
        # تسجيل أن هذا المستخدم يريد كتابة نص لهذا المعرف
        pending_writers[update.effective_user.id] = w_id
        await update.message.reply_text("أرسل همستك الآن (نميمتك).. رح توصل في سرية تامة 🤐")
        return True
    else:
        await update.message.reply_text("🚫 هذه الهمسة منتهية الصلاحية.")
        return True

async def receive_whisper_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # هل هذا المستخدم ينتظر كتابة همسة؟
    if user_id in pending_writers:
        w_id = pending_writers[user_id]
        text = update.message.text
        
        if w_id not in whispers_data:
            del pending_writers[user_id]
            await update.message.reply_text("❌ حدث خطأ، لم يتم العثور على بيانات الهمسة.")
            return

        # حفظ النص
        whispers_data[w_id]['text'] = text
        data = whispers_data[w_id]
        
        # إرسال الهمسة للقروب (زر فقط)
        kb = [[InlineKeyboardButton("📖 قراءة الهمسة", callback_data=f"read_w:{w_id}")]]
        await context.bot.send_message(
            chat_id=data['chat_id'],
            text=f"وصلت همسة جديدة! 🤫\nمن: مجهول (نعرفه 😎)\nإلى: [{data['to_name']}](tg://user?id={data['to_id']})\n\nفقط هو من يمكنه القراءة!",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown"
        )
        
        await update.message.reply_text("✅ تم إرسال الهمسة بنجاح!")
        del pending_writers[user_id] # حذف المستخدم من الانتظار

async def whisper_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if not data.startswith("read_w:"):
        return

    w_id = data.split(":")[1]
    user_id = query.from_user.id
    
    if w_id not in whispers_data:
        await query.answer("عذراً، هذه الهمسة قديمة أو محذوفة.", show_alert=True)
        return

    whisper = whispers_data[w_id]
    
    # التحقق: هل هو المستقبل أو المرسل؟
    if user_id == whisper['to_id'] or user_id == whisper['from_id']:
        await query.answer(f"الهمسة: {whisper['text']}", show_alert=True)
    else:
        # الرد باللهجة الجزائرية 😂
        await query.answer("النميمة خاطياتك! روح تلعب بعيد 😜", show_alert=True)
