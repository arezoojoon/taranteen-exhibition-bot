import os
import sqlite3 # Standard library for persistence
import json
import time # For simulation of scheduling
from fastapi import FastAPI, Request
import httpx
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

app = FastAPI()

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DB_NAME = "taranteen_leads.db"
BOOKING_URL = "https://taranteen.calendly.com/meeting"

# --- EXHIBITION & CONTACT INFO (UPDATED) ---
EXHIBITOR_NAME = "Hamidreza Damroodi"
EXHIBITOR_TITLE_FA = "مدیر عامل" # Updated
EXHIBITOR_TITLE_AR = "مدير المبيعات" 
EXHIBITOR_TITLE_RU = "Менеджер по продажам"
EXHIBITOR_TITLE_EN = "Sales Manager"
EXHIBITOR_PHONE = "+971564131033" # Updated
EXHIBITOR_EMAIL = "hr.damroodi@gmail.com" # Updated

# Optional: catalog URLs
CATALOG_1_URL = os.getenv("CATALOG_1_URL", "https://amhrd.com/wp-content/uploads/2025/11/JARRED-BOTTLED-Products-Catalog-P-4-compressed.pdf")
CATALOG_2_URL = os.getenv("CATALOG_2_URL", "https://amhrd.com/wp-content/uploads/2025/11/SEASONINGS-SPICES-Product-Catalog-P-8-compressed.pdf")
CATALOG_3_URL = os.getenv("CATALOG_3_URL", "https://amhrd.com/wp-content/uploads/2025/11/Dry-Goods-Snacks-Products-Catalog-P-1-compressed.pdf")
CATALOG_4_URL = os.getenv("CATALOG_4_URL", "https://amhrd.com/wp-content/uploads/2025/11/FROZEN-Products-Catalog-P-1-compressed.pdf")
CATALOG_5_URL = os.getenv("CATALOG_5_URL", "https://amhrd.com/wp-content/uploads/2025/11/MEAT-Products-Catalog-P-1-compressed.pdf")
CATALOG_6_URL = os.getenv("CATALOG_6_URL", "https://amhrd.com/wp-content/uploads/2025/11/CANNED-Products-Catalog-P-3-compressed.pdf")


# -------------------------------------------------
# DATABASE & STATE FUNCTIONS (NEW)
# -------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            chat_id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL,
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
    
    # Check if lead exists to update or insert
    cursor = conn.execute("SELECT * FROM leads WHERE chat_id = ?", (chat_id,))
    existing_lead = cursor.fetchone()

    if existing_lead:
        conn.execute("""
            UPDATE leads SET lang=?, name=?, phone=?, step=? WHERE chat_id=?
        """, (lang, name, phone, step, chat_id))
    else:
        conn.execute("""
            INSERT INTO leads (chat_id, lang, name, phone, registration_date, step) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chat_id, lang, name, phone, timestamp, step))

    conn.commit()
    conn.close()

def load_lead_state(chat_id):
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM leads WHERE chat_id = ?", (chat_id,))
    lead = cursor.fetchone()
    conn.close()
    if lead:
        # Convert sqlite3.Row object to a dictionary
        return dict(lead)
    return {'step': 'awaiting_lang_selection'} # Default starting state

# Call DB initialization when the app starts
init_db()

# -------------------------------------------------
# WHATSAPP & SCHEDULING (PLACEHOLDERS)
# -------------------------------------------------
def send_whatsapp_message(phone_number: str, message: str):
    """
    Placeholder: Sends a message via an external WhatsApp API (e.g., Twilio, Meta API).
    In a real system, this function would make an HTTP request to the external API.
    """
    print(f"--- WHATSAPP ACTION ---")
    print(f"Sending welcome message to {phone_number}: {message}")
    print(f"-----------------------")
    # Real implementation: httpx.post("WHATSAPP_API_URL", data=...)

def schedule_follow_up(chat_id: int, phone_number: str, lang: str):
    """
    Placeholder: Schedules a follow-up message to be sent after 3 days.
    In a real system, this requires a background task queue (e.g., Celery) 
    or a dedicated cron job to check the database for leads registered 3 days ago.
    """
    follow_up_message = {
        "fa": "سلام. تیم تارانتین پس از ۳ روز برای بررسی سفارش‌های شما در نمایشگاه پیام می‌دهد. مشتاق همکاری با شما هستیم!",
        "ar": "مرحبًا. يتواصل فريق تارينتين معك بعد 3 أيام لمتابعة طلباتك من المعرض. نتطلع إلى التعاون معك!",
        "ru": "Здравствуйте. Команда Taranteen свяжется с вами через 3 дня для оформления заказов с выставки. Мы рады сотрудничеству!",
        "en": "Hello. The Taranteen team is following up 3 days after your visit to the exhibition. We look forward to working with you!"
    }.get(lang, "Hello! Follow-up message from Taranteen.")
    
    print(f"--- SCHEDULING ACTION ---")
    print(f"Scheduled follow-up for {phone_number} in 3 days. Message: {follow_up_message}")
    # Real implementation: celery_app.send_task('send_scheduled_whatsapp', args=[phone_number, follow_up_message], countdown=3 * 24 * 60 * 60)

# -------------------------------------------------
# HELPERS (Same as previous step)
# -------------------------------------------------
async def send_message(chat_id: int, text: str, reply_markup: dict | None = None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def user_greeting(name: str, lang: str) -> str:
    if lang == "fa":
        return f"سلام {name}، "
    elif lang == "ar":
        return f"مرحباً {name}، "
    elif lang == "ru":
        return f"Привет, {name}, "
    else: # en
        return f"Hello {name}, "


def main_menu_keyboard(lang: str):
    if lang == "fa":
        return {
            "keyboard": [
                [{"text": "محصولات"}, {"text": "تخفیف‌ها و پیشنهادها"}],
                [{"text": "کاتالوگ‌ها"}, {"text": "مناطق و زمان تحویل"}],
                [{"text": "ثبت اطلاعات برای سفارش"}],
                [{"text": "ارتباط با غرفه‌دار"}, {"text": "رزرو ملاقات"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }
    elif lang == "ar":
        return {
            "keyboard": [
                [{"text": "المنتجات"}, {"text": "العروض والخصومات"}],
                [{"text": "الكتالوجات"}, {"text": "مناطق وأوقات التسليم"}],
                [{"text": "ترك بياناتي للطلب"}],
                [{"text": "التواصل مع العارض"}, {"text": "حجز موعد"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }
    elif lang == "ru":
        return {
            "keyboard": [
                [{"text": "Товары"}, {"text": "Скидки и предложения"}],
                [{"text": "Каталоги"}, {"text": "Зоны и время доставки"}],
                [{"text": "Оставить данные для заказа"}],
                [{"text": "Связаться со стендистом"}, {"text": "Записаться на встречу"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }
    else: # en
        return {
            "keyboard": [
                [{"text": "Products"}, {"text": "Offers & Discounts"}],
                [{"text": "Catalogs"}, {"text": "Delivery Areas & Times"}],
                [{"text": "Leave my details for order"}],
                [{"text": "Contact Exhibitor"}, {"text": "Book Appointment"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }

# (Catalogs messages functions remain the same for brevity)
def catalogs_message_fa() -> str:
    return (
        "کاتالوگ‌های فروشگاه مواد غذایی تارانتین:\n\n"
        f"۱) <a href=\"{CATALOG_1_URL}\">کاتالوگ ۱: محصولات شیشه‌ای و بطری</a>\n"
        f"۲) <a href=\"{CATALOG_2_URL}\">کاتالوگ ۲: ادویه‌جات و چاشنی‌ها</a>\n"
        f"۳) <a href=\"{CATALOG_3_URL}\">کاتالوگ ۳: خشکبار و تنقلات</a>\n"
        f"۴) <a href=\"{CATALOG_4_URL}\">کاتالوگ ۴: محصولات منجمد</a>\n"
        f"۵) <a href=\"{CATALOG_5_URL}\">کاتالوگ ۵: محصولات گوشتی</a>\n"
        f"۶) <a href=\"{CATALOG_6_URL}\">کاتالوگ ۶: کنسرویجات</a>\n"
    )

def catalogs_message_ar() -> str:
    return (
        "كتالوجات متجر بقالة تارينتين:\n\n"
        f"1) <a href=\"{CATALOG_1_URL}\">كتالوج 1: منتجات في برطمانات وزجاجات</a>\n"
        f"2) <a href=\"{CATALOG_2_URL}\">كتالوج 2: التوابل والبهارات</a>\n"
        f"3) <a href=\"{CATALOG_3_URL}\">كتالوج 3: السلع الجافة والوجبات الخفيفة</a>\n"
        f"4) <a href=\"{CATALOG_4_URL}\">كتالوج 4: المنتجات المجمدة</a>\n"
        f"5) <a href=\"{CATALOG_5_URL}\">كتالوج 5: منتجات اللحوم</a>\n"
        f"6) <a href=\"{CATALOG_6_URL}\">كتالوج 6: المعلبات</a>\n"
    )

def catalogs_message_ru() -> str:
    return (
        "Каталоги продуктового магазина Taranteen:\n\n"
        f"1) <a href=\"{CATALOG_1_URL}\">Каталог 1: Продукты в банках и бутылках</a>\n"
        f"2) <a href=\"{CATALOG_2_URL}\">Каталог 2: Приправы и специи</a>\n"
        f"3) <a href=\"{CATALOG_3_URL}\">Каталог 3: Сухие товары и закуски</a>\n"
        f"4) <a href=\"{CATALOG_4_URL}\">Каталог 4: Замороженные продукты</a>\n"
        f"5) <a href=\"{CATALOG_5_URL}\">Каталог 5: Мясные продукты</a>\n"
        f"6) <a href=\"{CATALOG_6_URL}\">Каталог 6: Консервы</a>\n"
    )

def catalogs_message_en() -> str:
    return (
        "Here are Taranteen catalogs:\n\n"
        f"1) <a href=\"{CATALOG_1_URL}\">Catalog 1: Jars & Bottles</a>\n"
        f"2) <a href=\"{CATALOG_2_URL}\">Catalog 2: Seasonings & Spices</a>\n"
        f"3) <a href=\"{CATALOG_3_URL}\">Catalog 3: Dry Goods & Snacks</a>\n"
        f"4) <a href=\"{CATALOG_4_URL}\">Catalog 4: Frozen Products</a>\n"
        f"5) <a href=\"{CATALOG_5_URL}\">Catalog 5: Meat Products</a>\n"
        f"6) <a href=\"{CATALOG_6_URL}\">Catalog 6: Canned Products</a>\n"
    )


# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Taranteen Grocery Bot running"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return {"ok": True}

    # Load state from DB
    lead_state = load_lead_state(chat_id)
    lang = lead_state.get("lang")
    name = lead_state.get("name", "User") 
    phone = lead_state.get("phone")
    current_step = lead_state.get('step')


    # ---------------- /start (Initial prompt for language) ----------------
    if text.startswith("/start"):
        # Reset state and ask for language
        save_lead_state(chat_id, '', '', '', 'awaiting_lang_selection')
        
        greeting = (
            "Welcome to <b>Taranteen</b> 🛒\n"
            "Online grocery and food products.\n\n"
            "Choose a language / إختر لغة / زبان را انتخاب کنید / Выберите язык:\n"
        )
        lang_keyboard = {
            "keyboard": [
                [{"text": "English (EN)"}, {"text": "Русский (RU)"}],
                [{"text": "فارسی (FA)"}, {"text": "العربية (AR)"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        await send_message(chat_id, greeting, reply_markup=lang_keyboard)
        return {"ok": True}

    # ---------------- State 1: Language Selection ----------------
    if current_step == 'awaiting_lang_selection':
        selected_lang = None
        prompt_msg = ""
        
        if "EN" in text.upper():
            selected_lang = "en"
            prompt_msg = "Thank you. Please send your full name:"
        elif "FA" in text.upper() or "فارسی" in text:
            selected_lang = "fa"
            prompt_msg = "ممنون. لطفاً نام کامل خود را بفرستید:"
        elif "AR" in text.upper() or "العربية" in text:
            selected_lang = "ar"
            prompt_msg = "شكراً. الرجاء إرسال اسمك الكامل:"
        elif "RU" in text.upper() or "РУССКИЙ" in text or "RUSSIAN" in text.upper():
            selected_lang = "ru"
            prompt_msg = "Спасибо. Пожалуйста, отправьте свое полное имя:"
        
        if selected_lang:
            save_lead_state(chat_id, selected_lang, '', '', 'awaiting_name') # Save lang, next step: awaiting_name
            await send_message(chat_id, prompt_msg)
            return {"ok": True}
        else:
            await send_message(chat_id, "Invalid selection. Please choose a language from the options.")
            return {"ok": True}

    # ---------------- State 2: Awaiting Name ----------------
    if current_step == 'awaiting_name':
        # Save name and move to phone prompt
        name_input = text
        save_lead_state(chat_id, lang, name_input, '', 'awaiting_phone')
        
        prompt = (
            f"Thank you, {name_input}. Now, please send your WhatsApp number (e.g., +971501234567):"
            if lang == "en" else
            f"ممنون، {name_input}. اکنون، لطفاً شماره واتساپ خود را بفرستید (مثال: ۰۵۰۱۲۳۴۵۶۷):"
            if lang == "fa" else
            f"شكراً لك، {name_input}. الآن، الرجاء إرسال رقم واتساب الخاص بك (مثال: ٠٥٠١٢٣٤٥٦٧):"
            if lang == "ar" else
            f"Спасибо, {name_input}. Теперь, пожалуйста, отправьте свой номер WhatsApp (например: +971501234567):"
        )
        
        await send_message(chat_id, prompt)
        return {"ok": True}

    # ---------------- State 3: Awaiting Phone ----------------
    if current_step == 'awaiting_phone':
        # Save phone, set final step, and greet user
        phone_input = text
        
        # We need to reload the state to get the name saved in the previous step
        lead_state = load_lead_state(chat_id)
        current_name = lead_state.get('name', 'User')

        save_lead_state(chat_id, lang, current_name, phone_input, 'main_menu') 
        
        # --- NEW WHATSAPP ACTIONS ---
        welcome_whatsapp_message = {
            "fa": f"سلام {current_name} عزیز. از ثبت اطلاعاتتان در غرفه تارانتین ممنونیم. کاتالوگ‌های ما را می‌توانید از طریق لینک‌های زیر مشاهده کنید.",
            "ar": f"مرحباً {current_name}. شكراً لتسجيل بياناتك في جناح تارينتين. يمكنك الاطلاع على كتالوجاتنا عبر الروابط التالية.",
            "ru": f"Здравствуйте, {current_name}. Спасибо за регистрацию на стенде Taranteen. Наши каталоги доступны по ссылкам ниже.",
            "en": f"Hello {current_name}. Thank you for registering your details at the Taranteen booth. You can view our catalogs via the links below."
        }.get(lang, f"Hello {current_name}. Welcome to Taranteen.")
        
        send_whatsapp_message(phone_input, welcome_whatsapp_message)
        schedule_follow_up(chat_id, phone_input, lang)
        # ----------------------------

        welcome_msg = (
            f"Thank you, {current_name} 👋. Welcome to Taranteen online grocery.\n"
            "Your details have been saved for follow-up. A **welcome message has been sent to your WhatsApp**. Please choose an option below:"
            if lang == "en" else
            f"ممنون، {current_name} 👋. به چت‌بات فروشگاه مواد غذایی تارانتین خوش آمدید.\n"
            "اطلاعات شما برای پیگیری ذخیره شد. **پیام خوش‌آمدگویی به واتساپ شما ارسال شد**. از منوی زیر یکی از گزینه‌ها را انتخاب کنید:"
            if lang == "fa" else
            f"شكراً لك، {current_name} 👋. مرحباً بك في بقالة تارينتين عبر الإنترنت.\n"
            "تم حفظ بياناتك للمتابعة. **تم إرسال رسالة ترحيب إلى واتساب الخاص بك**. الرجاء اختيار خيار أدناه:"
            if lang == "ar" else
            f"Спасибо, {current_name} 👋. Добро пожаловать в онлайн-магазин Taranteen.\n"
            "Ваши данные сохранены для обратной связи. **Приветственное сообщение было отправлено вам в WhatsApp**. Пожалуйста, выберите один из вариантов ниже:"
        )

        await send_message(chat_id, welcome_msg, reply_markup=main_menu_keyboard(lang))
        return {"ok": True}


    # If not in one of the initial states, proceed with main menu logic
    if current_step != 'main_menu':
        # If the user is mid-flow but sends arbitrary text, ask them to continue the flow
        prompt = {
            "fa": "لطفاً ابتدا روند ثبت اطلاعات (نام و شماره) را تکمیل کنید.",
            "ar": "الرجاء إكمال عملية تسجيل البيانات (الاسم والرقم) أولاً.",
            "ru": "Пожалуйста, сначала завершите процесс регистрации (имя и номер).",
            "en": "Please complete the registration process (name and number) first."
        }.get(lang or 'en')
        await send_message(chat_id, prompt)
        return {"ok": True}

    # --- MAIN MENU FLOWS (FA, AR, RU, EN) ---
    
    # Flow logic uses the loaded `lang`, `name`, and `phone` variables
    
    # --- FA FLOWS ---
    if lang == "fa":
        if text == "ارتباط با غرفه‌دار":
            msg = (
                f"{user_greeting(name, 'fa')}"
                "برای ارتباط مستقیم با **مدیر عامل** ما:\n"
                f"• نام: {EXHIBITOR_NAME} ({EXHIBITOR_TITLE_FA})\n"
                f"• واتساپ: <a href='https://wa.me/{EXHIBITOR_PHONE}'>{EXHIBITOR_PHONE}</a>\n"
                f"• ایمیل: {EXHIBITOR_EMAIL}\n"
                "می‌توانید همین حالا با ایشان تماس بگیرید."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}
        
        if text == "رزرو ملاقات":
            msg = (
                f"{user_greeting(name, 'fa')}"
                "برای رزرو وقت ملاقات خصوصی با مدیران ما در غرفه:\n"
                f"لطفاً از طریق این لینک، زمان مورد نظر خود را در تقویم ما انتخاب کنید:\n"
                f"🗓️ <a href='{BOOKING_URL}'>رزرو وقت ملاقات تارانتین</a>\n"
                "ما منتظر دیدار شما هستیم!"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}
            
        if text == "محصولات":
            msg = (
                f"{user_greeting(name, 'fa')}"
                "در تارانتین می‌تونید انواع مواد غذایی، محصولات تازه، کنسروی، نوشیدنی‌ها "
                "و اقلام روزمره خانه را سفارش بدهید.\n\n"
                "برای مشاهده دسته‌بندی محصولات و ثبت سفارش، می‌توانید از کاتالوگ‌های بخش بعدی استفاده کنید."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "تخفیف‌ها و پیشنهادها":
            msg = (
                f"{user_greeting(name, 'fa')}"
                "اطلاعات تخفیف‌ها و پیشنهادهای ویژه این هفته به زودی در همین بخش به‌روزرسانی می‌شوند.\n"
                "در حال حاضر، می‌توانید از طریق دکمه **کاتالوگ‌ها** محصولات ما را مشاهده کنید."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "کاتالوگ‌ها":
            msg = catalogs_message_fa()
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "مناطق و زمان تحویل":
            msg = (
                f"{user_greeting(name, 'fa')}"
                "تحویل سفارش‌ها در مناطق مشخص‌شده در شهر **دبی** صورت می‌گیرد.\n"
                "زمان‌های تحویل: **صبح (۹ تا ۱۲)**، **بعدازظهر (۱ تا ۵)**، **شب (۶ تا ۹)**.\n"
                "برای هماهنگی‌های خاص جهت تحویل رستوران‌ها و فروشگاه‌ها، لطفاً از بخش **ثبت اطلاعات برای سفارش** با ما در ارتباط باشید."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "ثبت اطلاعات برای سفارش":
            msg = (
                f"{user_greeting(name, 'fa')}"
                "برای اینکه تیم تارانتین بتواند سفارش یا درخواست همکاری شما را پیگیری کند، "
                "لطفاً اطلاعات زیر را در یک پیام **دیگر** ارسال کنید تا به تیم فروش منتقل شود:\n\n"
                f"۱. نام کامل: **{name}**\n"
                f"۲. شماره واتساپ: **{phone}**\n"
                "۳. نوع مشتری (خانواده / رستوران / سوپرمارکت و ...)\n"
                "۴. لیست اقلام درخواستی یا سؤالات شما"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        # any other FA text after that
        msg = (
            f"{user_greeting(name, 'fa')}"
            "پیام شما با موفقیت برای تیم فروش تارانتین ارسال شد 🙏\n"
            "کارشناسان ما به زودی برای پیگیری سفارش یا همکاری با شما تماس خواهند گرفت.\n"
            "برای دیدن دوباره منو، از دکمه‌های پایین استفاده کنید."
        )
        await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
        return {"ok": True}

    # --- AR FLOWS ---
    elif lang == "ar":
        if text == "التواصل مع العارض":
            msg = (
                f"{user_greeting(name, 'ar')}"
                "للتواصل مباشرة مع مدير المبيعات لدينا:\n"
                f"• الاسم: {EXHIBITOR_NAME} ({EXHIBITOR_TITLE_AR})\n"
                f"• واتساب: <a href='https://wa.me/{EXHIBITOR_PHONE}'>{EXHIBITOR_PHONE}</a>\n"
                f"• البريد الإلكتروني: {EXHIBITOR_EMAIL}\n"
                "يمكنك الاتصال به الآن."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}
        
        if text == "حجز موعد":
            msg = (
                f"{user_greeting(name, 'ar')}"
                "لحجز موعد خاص مع مديرينا في الجناح:\n"
                f"الرجاء اختيار الوقت المناسب لك في تقويمنا عبر هذا الرابط:\n"
                f"🗓️ <a href='{BOOKING_URL}'>حجز موعد تارينتين</a>\n"
                "نحن نتطلع إلى رؤيتك!"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}
            
        if text == "المنتجات":
            msg = (
                f"{user_greeting(name, 'ar')}"
                "تقدم تارينتين مجموعة واسعة من مواد البقالة: المنتجات الطازجة، مواد المؤن، "
                "المشروبات والأساسيات اليومية.\n\n"
                "لعرض فئات المنتجات وتقديم طلب، يمكنك استخدام الكتالوجات في القسم التالي."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}

        if text == "العروض والخصومات":
            msg = (
                f"{user_greeting(name, 'ar')}"
                "سيتم تحديث معلومات العروض والخصومات الخاصة بهذا الأسبوع قريباً في هذا القسم.\n"
                "في الوقت الحالي، يمكنك عرض منتجاتنا عبر زر **الكتالوجات**."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}

        if text == "الكتالوجات":
            msg = catalogs_message_ar()
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}

        if text == "مناطق وأوقات التسليم":
            msg = (
                f"{user_greeting(name, 'ar')}"
                "يتم توصيل الطلبات في مناطق محددة داخل مدينة **دبي**.\n"
                "فترات التسليم: **صباحاً (9 صباحاً - 12 ظهراً)**، **بعد الظهر (1 ظهراً - 5 مساءً)**، **مساءً (6 مساءً - 9 مساءً)**.\n"
                "لترتيبات التوصيل الخاصة للمطاعم والمحلات، يرجى التواصل معنا عبر قسم **ترك بياناتي للطلب**."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}

        if text == "ترك بياناتي للطلب":
            msg = (
                f"{user_greeting(name, 'ar')}"
                "حتى يتمكن فريق تارينتين من متابعة طلبك أو طلب الشراكة، "
                "الرجاء إرسال المعلومات التالية في رسالة **أخرى** ليتم توجيهها إلى فريق المبيعات:\n\n"
                f"1) الاسم الكامل: **{name}**\n"
                f"2) رقم واتساب: **{phone}**\n"
                "3) نوع العميل (عائلة / مطعم / سوبر ماركت / غير ذلك)\n"
                "4) قائمة الأصناف المطلوبة أو استفساراتك"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
            return {"ok": True}

        # any other AR text after that
        msg = (
            f"{user_greeting(name, 'ar')}"
            "تم إرسال رسالتك بنجاح إلى فريق مبيعات تارينتين 🙏\n"
            "سيتصل بك خبراؤنا قريباً لمتابعة طلبك أو شراكتك.\n"
            "اضغط على أحد الأزرار أدناه لفتح القائمة مرة أخرى."
        )
        await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ar"))
        return {"ok": True}

    # --- RU FLOWS ---
    elif lang == "ru":
        if text == "Связаться со стендистом":
            msg = (
                f"{user_greeting(name, 'ru')}"
                "Для прямого контакта с нашим менеджером по продажам:\n"
                f"• Имя: {EXHIBITOR_NAME} ({EXHIBITOR_TITLE_RU})\n"
                f"• WhatsApp: <a href='https://wa.me/{EXHIBITOR_PHONE}'>{EXHIBITOR_PHONE}</a>\n"
                f"• Email: {EXHIBITOR_EMAIL}\n"
                "Вы можете связаться с ним прямо сейчас."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        if text == "Записаться на встречу":
            msg = (
                f"{user_greeting(name, 'ru')}"
                "Чтобы забронировать частную встречу с нашими менеджерами на стенде:\n"
                f"Пожалуйста, выберите удобное для вас время в нашем календаре по этой ссылке:\n"
                f"🗓️ <a href='{BOOKING_URL}'>Запись на встречу Taranteen</a>\n"
                "Мы с нетерпением ждем встречи с вами!"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        if text == "Товары":
            msg = (
                f"{user_greeting(name, 'ru')}"
                "Taranteen предлагает широкий ассортимент продуктов: свежие продукты, бакалею, "
                "напитки и товары первой необходимости.\n\n"
                "Чтобы просмотреть категории товаров и оформить заказ, пожалуйста, воспользуйтесь каталогами в следующем разделе."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        if text == "Скидки и предложения":
            msg = (
                f"{user_greeting(name, 'ru')}"
                "Информация о скидках и специальных предложениях на этой неделе скоро будет обновлена в этом разделе.\n"
                "В настоящее время вы можете просмотреть наши товары с помощью кнопки **Каталоги**."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        if text == "Каталоги":
            msg = catalogs_message_ru()
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        if text == "Зоны и время доставки":
            msg = (
                f"{user_greeting(name, 'ru')}"
                "Доставка заказов осуществляется в определенных районах **Дубая**.\n"
                "Временные интервалы доставки: **Утро (9:00 - 12:00)**, **День (13:00 - 17:00)**, **Вечер (18:00 - 21:00)**.\n"
                "Для специальных условий доставки для ресторанов и магазинов, пожалуйста, свяжитесь с нами через раздел **Оставить данные для заказа**."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        if text == "Оставить данные для заказа":
            msg = (
                f"{user_greeting(name, 'ru')}"
                "Чтобы команда Taranteen могла обработать ваш заказ или запрос на партнерство, "
                "пожалуйста, отправьте следующую информацию **отдельным** сообщением, чтобы она была перенаправлена в отдел продаж:\n\n"
                f"1) Ваше полное имя: **{name}**\n"
                f"2) Номер WhatsApp: **{phone}**\n"
                "3) Тип клиента (семья / ресторан / супермаркет / другое)\n"
                "4) Список запрашиваемых товаров или ваши вопросы"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
            return {"ok": True}

        # any other RU text after that
        msg = (
            f"{user_greeting(name, 'ru')}"
            "Ваше сообщение успешно отправлено отделу продаж Taranteen 🙏\n"
            "Наши специалисты свяжутся с вами в ближайшее время для уточнения заказа или партнерства.\n"
            "Нажмите одну из кнопок ниже, чтобы снова открыть меню."
        )
        await send_message(chat_id, msg, reply_markup=main_menu_keyboard("ru"))
        return {"ok": True}

    # --- EN FLOWS ---
    elif lang == "en":
        if text == "Contact Exhibitor":
            msg = (
                f"{user_greeting(name, 'en')}"
                "To contact our Sales Manager directly:\n"
                f"• Name: {EXHIBITOR_NAME} ({EXHIBITOR_TITLE_EN})\n"
                f"• WhatsApp: <a href='https://wa.me/{EXHIBITOR_PHONE}'>{EXHIBITOR_PHONE}</a>\n"
                f"• Email: {EXHIBITOR_EMAIL}\n"
                "Feel free to reach out now."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Book Appointment":
            msg = (
                f"{user_greeting(name, 'en')}"
                "To book a private appointment with our managers at the booth:\n"
                f"Please choose your preferred time in our calendar via this link:\n"
                f"🗓️ <a href='{BOOKING_URL}'>Taranteen Appointment Booking</a>\n"
                "We look forward to seeing you!"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Products":
            msg = (
                f"{user_greeting(name, 'en')}"
                "Taranteen offers a wide range of grocery items: fresh products, pantry items, "
                "drinks and everyday essentials.\n\n"
                "To view product categories and place an order, please use the catalogs in the next section."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Offers & Discounts":
            msg = (
                f"{user_greeting(name, 'en')}"
                "Information on this week's offers and discounts will be updated in this section shortly.\n"
                "Currently, you can view our products through the **Catalogs** button."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Catalogs":
            msg = catalogs_message_en()
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Delivery Areas & Times":
            msg = (
                f"{user_greeting(name, 'en')}"
                "Orders are delivered in defined areas within **Dubai**.\n"
                "Delivery time slots: **Morning (9 AM - 12 PM)**, **Afternoon (1 PM - 5 PM)**, **Evening (6 PM - 9 PM)**.\n"
                "For special delivery arrangements for restaurants and shops, please contact us via the **Leave my details for order** section."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Leave my details for order":
            msg = (
                f"{user_greeting(name, 'en')}"
                "For the Taranteen team to follow up on your order or partnership inquiry, "
                "please send the following information in **another** message to be forwarded to the sales team:\n\n"
                f"1) Your full name: **{name}**\n"
                f"2) WhatsApp number: **{phone}**\n"
                "3) Customer type (family / restaurant / supermarket / other)\n"
                "4) List of requested items or your questions"
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        # any other EN text after that
        msg = (
            f"{user_greeting(name, 'en')}"
            "Thank you for your message 🙏\n"
            "Your message has been successfully sent to the Taranteen sales team.\n"
            "Our experts will contact you shortly to follow up on your order or partnership.\n"
            "Tap one of the buttons below to open the menu again."
        )
        await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
        return {"ok": True}

    return {"ok": True}
