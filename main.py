# main.py
import logging
import pytz
import apscheduler.util
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from plugins.football import start_match, match_engine # استيراد دوال الكرة من الملف المنفصل

# --- إصلاح التوقيت (Termux Fix) ---
def forced_astimezone(timezone):
    return pytz.utc
apscheduler.util.astimezone = forced_astimezone

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR)

if __name__ == '__main__':
    print("🚀 جاري تشغيل البوت بنظام الملفات المتعددة...")
    
    # بناء التطبيق
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # === تسجيل المعالجات (Handlers) ===
    
    # 1. قسم كرة القدم (يتم جلبه من plugins/football.py)
    app.add_handler(CommandHandler("match", start_match))
    app.add_handler(MessageHandler(filters.Regex("^(مباراة|لعب)$"), start_match))
    app.add_handler(CallbackQueryHandler(match_engine, pattern="^match:"))

    # هنا سنضيف لاحقاً بقية الملفات (الاستوديو، التعليم، إلخ) بنفس الطريقة
    
    print("✅ البوت يعمل الآن!")
    app.run_polling()
