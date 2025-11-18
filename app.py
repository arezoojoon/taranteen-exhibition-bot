import os
import sqlite3
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# تنظیمات CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DB_NAME = "taranteen_leads.db"
BOOKING_URL = "https://taranteen.calendly.com/meeting"

# اطلاعات غرفه‌دار
EXHIBITOR_NAME = "Hamidreza Damroodi"
EXHIBITOR_PHONE = "+971564131033"
EXHIBITOR_EMAIL = "hr.damroodi@gmail.com"

# بازگرداندن لینک‌های ۶ کاتالوگ
CATALOG_1_URL = os.getenv("CATALOG_1_URL", "https://amhrd.com/wp-content/uploads/2025/11/JARRED-BOTTLED-Products-Catalog-P-4-compressed.pdf")
CATALOG_2_URL = os.getenv("CATALOG_2_URL", "https://amhrd.com/wp-content/uploads/2025/11/SEASONINGS-SPICES-Product-Catalog-P-8-compressed.pdf")
CATALOG_3_URL = os.getenv("CATALOG_3_URL", "https://amhrd.com/wp-content/uploads/2025/11/Dry-Goods-Snacks-Products-Catalog-P-1-compressed.pdf")
CATALOG_4_URL = os.getenv("CATALOG_4_URL", "https://amhrd.com/wp-content/uploads/2025/11/FROZEN-Products-Catalog-P-1-compressed.pdf")
CATALOG_5_URL = os.getenv("CATALOG_5_URL", "https://amhrd.com/wp-content/uploads/2025/11/MEAT-Products-Catalog-P-1-compressed.pdf")
CATALOG_6_URL = os.getenv("CATALOG_6_URL", "https://amhrd.com/wp-content/uploads/2025/11/CANNED-Products-Catalog-P-3-compressed.pdf")

# --- DATABASE ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            chat_id TEXT PRIMARY KEY,
            lang TEXT,
            name TEXT,
            phone TEXT,
            registration_date INTEGER,
            step TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_lead_state(chat_id, lang, name, phone, step):
    conn = get_db_connection()
    timestamp = int(time.time())
    cursor = conn.execute("SELECT * FROM leads WHERE chat_id = ?", (str(chat_id),))
    if cursor.fetchone():
        conn.execute("""
            UPDATE leads 
            SET lang=COALESCE(?, lang), name=COALESCE(?, name), phone=COALESCE(?, phone), step=? 
            WHERE chat_id=?
        """, (lang or None, name or None, phone or None, step, str(chat_id)))
    else:
        conn.execute("INSERT INTO leads (chat_id, lang, name, phone, registration_date, step) VALUES (?, ?, ?, ?, ?, ?)", 
                     (str(chat_id), lang, name, phone, timestamp, step))
    conn.commit()
    conn.close()

def load_lead_state(chat_id):
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM leads WHERE chat_id = ?", (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    if row: return dict(row)
    return {'step': 'awaiting_lang_selection', 'lang': None}

init_db()

# --- HELPERS ---
def get_catalogs_message(lang):
    # عنوان‌ها بر اساس زبان
    titles = {
        "en": ["Jars & Bottles", "Seasonings & Spices", "Dry Goods & Snacks", "Frozen Products", "Meat Products", "Canned Products"],
        "fa": ["محصولات شیشه‌ای", "ادویه و چاشنی", "خشکبار و تنقلات", "محصولات منجمد", "محصولات گوشتی", "کنسرویجات"],
        "ar": ["الجرار والزجاجات", "التوابل والبهارات", "السلع الجافة", "المنتجات المجمدة", "منتجات اللحوم", "المعلبات"],
        "ru": ["Банки и бутылки", "Приправы и специи", "Сухие товары", "Замороженные продукты", "Мясные продукты", "Консервы"]
    }
    t = titles.get(lang, titles["en"])
    
    # ساخت لیست لینک‌ها
    msg = ""
    msg += f"1) <a href='{CATALOG_1_URL}'>{t[0]}</a>\n"
    msg += f"2) <a href='{CATALOG_2_URL}'>{t[1]}</a>\n"
    msg += f"3) <a href='{CATALOG_3_URL}'>{t[2]}</a>\n"
    msg += f"4) <a href='{CATALOG_4_URL}'>{t[3]}</a>\n"
    msg += f"5) <a href='{CATALOG_5_URL}'>{t[4]}</a>\n"
    msg += f"6) <a href='{CATALOG_6_URL}'>{t[5]}</a>"
    
    intro = {
        "en": "Here are our catalogs:",
        "fa": "لیست کاتالوگ‌های ما:",
        "ar": "قائمة الكتالوجات:",
        "ru": "Наши каталоги:"
    }.get(lang, "Catalogs:")
    
    return f"{intro}\n\n{msg}"

# --- LOGIC ---
async def process_user_input(chat_id: str, text: str, responder_func):
    state = load_lead_state(chat_id)
    step = state.get('step')
    lang = state.get('lang')

    # ریست کردن
    if text in ["/start", "start", "شروع"]:
        save_lead_state(chat_id, '', '', '', 'awaiting_lang_selection')
        await responder_func(
            "Welcome to <b>Taranteen</b> 🛒\nChoose a language / انتخاب زبان:", 
            options=["English (EN)", "فارسی (FA)", "العربية (AR)", "Русский (RU)"]
        )
        return

    # مرحله ۱: زبان
    if step == 'awaiting_lang_selection':
        sel_lang = None
        if "EN" in text.upper(): sel_lang = "en"
        elif "FA" in text.upper() or "فارسی" in text: sel_lang = "fa"
        elif "AR" in text.upper() or "العربية" in text: sel_lang = "ar"
        elif "RU" in text.upper() or "РУССКИЙ" in text: sel_lang = "ru"

        if sel_lang:
            save_lead_state(chat_id, sel_lang, '', '', 'awaiting_name')
            prompt = {
                "en": "Thank you. Please send your full name:",
                "fa": "ممنون. لطفاً نام کامل خود را وارد کنید:",
                "ar": "شكراً. الرجاء إرسال اسمك الكامل:",
                "ru": "Спасибо. Пожалуйста, введите ваше полное имя:"
            }[sel_lang]
            await responder_func(prompt)
        else:
            await responder_func("Please select a language:", options=["English (EN)", "فارسی (FA)"])
        return

    # مرحله ۲: نام
    if step == 'awaiting_name':
        save_lead_state(chat_id, lang, text, '', 'awaiting_phone')
        prompt = {
            "en": f"Nice to meet you, {text}. Now please send your WhatsApp number:",
            "fa": f"خوشبختم {text}. حالا لطفاً شماره واتساپ خود را بفرستید:",
            "ar": f"تشرفنا {text}. الآن أرسل رقم الواتساب:",
            "ru": f"Приятно познакомиться, {text}. Теперь отправьте номер WhatsApp:"
        }.get(lang, "Send phone:")
        await responder_func(prompt)
        return

    # مرحله ۳: شماره و اتمام
    if step == 'awaiting_phone':
        save_lead_state(chat_id, lang, state.get('name'), text, 'main_menu')
        welcome = {
            "en": "Registration Complete! How can we help?",
            "fa": "ثبت نام کامل شد! چطور می‌توانیم کمکتان کنیم؟",
            "ar": "اكتمل التسجيل! كيف يمكننا مساعدتك؟",
            "ru": "Регистрация завершена! Чем можем помочь?"
        }.get(lang, "Done.")
        await responder_func(welcome, options=get_main_menu_options(lang))
        return

    # مرحله ۴: منوی اصلی
    if step == 'main_menu':
        # گزینه ۱: کاتالوگ‌ها
        if any(x in text for x in ["Catalogs", "کاتالوگ", "الكتالوجات", "Каталоги"]):
            msg = get_catalogs_message(lang)
            await responder_func(msg, options=get_main_menu_options(lang))
        
        # گزینه ۲: تماس
        elif any(x in text for x in ["Contact", "ارتباط", "التواصل", "Связаться"]):
            titles = {"en": "Sales Manager", "fa": "مدیر عامل", "ar": "مدير المبيعات", "ru": "Менеджер по продажам"}
            t = titles.get(lang, "Manager")
            info = f"👤 {EXHIBITOR_NAME} ({t})\n📞 {EXHIBITOR_PHONE}\n📧 {EXHIBITOR_EMAIL}"
            intro = {
                "en": "You can contact our manager directly:",
                "fa": "اطلاعات تماس مستقیم با مدیریت:",
                "ar": "يمكنك التواصل مع المدير مباشرة:",
                "ru": "Вы можете связаться с менеджером напрямую:"
            }.get(lang, "")
            await responder_func(f"{intro}\n\n{info}", options=get_main_menu_options(lang))

        # گزینه ۳: رزرو
        elif any(x in text for x in ["Book", "رزرو", "حجز", "Записаться"]):
            msg = {
                "en": f"Book a meeting here: <a href='{BOOKING_URL}'>Calendly</a>",
                "fa": f"برای رزرو وقت ملاقات کلیک کنید: <a href='{BOOKING_URL}'>لینک رزرو</a>",
                "ar": f"احجز موعداً هنا: <a href='{BOOKING_URL}'>رابط الحجز</a>",
                "ru": f"Запишитесь на встречу здесь: <a href='{BOOKING_URL}'>Calendly</a>"
            }.get(lang, BOOKING_URL)
            await responder_func(msg, options=get_main_menu_options(lang))

        else:
            fallback = {
                "en": "Please choose an option from the menu.",
                "fa": "لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                "ar": "الرجاء اختيار خيار من القائمة.",
                "ru": "Пожалуйста, выберите опцию из меню."
            }.get(lang, "Please choose an option.")
            await responder_func(fallback, options=get_main_menu_options(lang))
        return

    await responder_func("Type /start to restart.")

def get_main_menu_options(lang):
    if lang == 'fa': return ["کاتالوگ‌ها", "ارتباط با غرفه‌دار", "رزرو ملاقات"]
    if lang == 'ar': return ["الكتالوجات", "التواصل مع العارض", "حجز موعد"]
    if lang == 'ru': return ["Каталоги", "Связаться", "Записаться"]
    return ["Catalogs", "Contact Exhibitor", "Book Appointment"]

# --- ROUTES ---
@app.get("/")
async def root():
    return {"status": "ok", "message": "Taranteen Grocery Bot is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    if not chat_id: return {"ok": True}
    async def telegram_responder(resp_text, options=None):
        payload = {"chat_id": chat_id, "text": resp_text, "parse_mode": "HTML"}
        if options:
            payload["reply_markup"] = {"keyboard": [[{"text": o}] for o in options], "resize_keyboard": True}
        async with httpx.AsyncClient() as client:
            await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
    await process_user_input(str(chat_id), text, telegram_responder)
    return {"ok": True}

class WebMessage(BaseModel):
    session_id: str
    message: str

@app.post("/web-chat")
async def web_chat(body: WebMessage):
    responses = []
    async def web_responder(resp_text, options=None):
        responses.append({"text": resp_text, "options": options or []})
    await process_user_input(body.session_id, body.message, web_responder)
    return {"messages": responses}
