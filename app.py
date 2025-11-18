import os
from fastapi import FastAPI, Request
import httpx
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

app = FastAPI()

# -------------------------------------------------
# STATE MANAGEMENT
# ذخیره موقت اطلاعات کاربر در حافظه: {chat_id: {'lang': str, 'name': str, 'phone': str, 'step': str}}
USER_STATE = {}
# -------------------------------------------------


# -------------------------------------------------
# CONFIG
# -------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Optional: catalog URLs (پر می‌کنی یا خالی می‌گذاری)
# این لینک‌ها باید به کاتالوگ‌های واقعی شما اشاره کنند.
CATALOG_1_URL = os.getenv("CATALOG_1_URL", "https://amhrd.com/wp-content/uploads/2025/11/JARRED-BOTTLED-Products-Catalog-P-4-compressed.pdf")
CATALOG_2_URL = os.getenv("CATALOG_2_URL", "https://amhrd.com/wp-content/uploads/2025/11/SEASONINGS-SPICES-Product-Catalog-P-8-compressed.pdf")
CATALOG_3_URL = os.getenv("CATALOG_3_URL", "https://amhrd.com/wp-content/uploads/2025/11/Dry-Goods-Snacks-Products-Catalog-P-1-compressed.pdf")
CATALOG_4_URL = os.getenv("CATALOG_4_URL", "https://amhrd.com/wp-content/uploads/2025/11/FROZEN-Products-Catalog-P-1-compressed.pdf")
CATALOG_5_URL = os.getenv("CATALOG_5_URL", "https://amhrd.com/wp-content/uploads/2025/11/MEAT-Products-Catalog-P-1-compressed.pdf")
CATALOG_6_URL = os.getenv("CATALOG_6_URL", "https://amhrd.com/wp-content/uploads/2025/11/CANNED-Products-Catalog-P-3-compressed.pdf")


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
async def send_message(chat_id: int, text: str, reply_markup: dict | None = None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)


def user_greeting(name: str, lang: str) -> str:
    """Creates a personalized greeting based on language."""
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
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }


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

    # Retrieve user state
    user_state = USER_STATE.get(chat_id, {})
    lang = user_state.get("lang")
    name = user_state.get("name", "User") # Default to 'User'

    # ---------------- /start (Initial prompt for language) ----------------
    if text.startswith("/start"):
        # Reset state and ask for language
        USER_STATE[chat_id] = {'step': 'awaiting_lang_selection'}
        
        greeting = (
            "Welcome to <b>Taranteen</b> 🛒\n"
            "Online grocery and food products.\n\n"
            "Choose a language / إختر لغة / زبان را انتخاب کنید / Выберите язык:\n"
        )
        # Custom keyboard for language selection
        lang_keyboard = {
            "keyboard": [
                [{"text": "English (EN)"}, {"text": "Русский (RU)"}], # Added RU
                [{"text": "فارسی (FA)"}, {"text": "العربية (AR)"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }
        await send_message(chat_id, greeting, reply_markup=lang_keyboard)
        return {"ok": True}

    # ---------------- State 1: Language Selection ----------------
    if user_state.get('step') == 'awaiting_lang_selection':
        selected_lang = None
        prompt_msg = ""
        
        if "EN" in text.upper():
            selected_lang = "en"
            prompt_msg = "Please send your full name and WhatsApp number in one message (e.g., John Doe, +971501234567):"
        elif "FA" in text.upper() or "فارسی" in text:
            selected_lang = "fa"
            prompt_msg = "لطفاً نام کامل و شماره واتساپ خود را در یک پیام بفرستید (مثال: سارا محمدی، ۰۵۰۱۲۳۴۵۶۷):"
        elif "AR" in text.upper() or "العربية" in text:
            selected_lang = "ar"
            prompt_msg = "الرجاء إرسال اسمك الكامل ورقم واتساب في رسالة واحدة (مثال: علي خالد، ٠٥٠١٢٣٤٥٦٧):"
        elif "RU" in text.upper() or "РУССКИЙ" in text or "RUSSIAN" in text.upper():
            selected_lang = "ru"
            prompt_msg = "Пожалуйста, отправьте свое полное имя и номер WhatsApp в одном сообщении (например: Иван Петров, +971501234567):"
        
        if selected_lang:
            USER_STATE[chat_id]['lang'] = selected_lang
            USER_STATE[chat_id]['step'] = 'awaiting_details'
            await send_message(chat_id, prompt_msg)
            return {"ok": True}
        else:
            await send_message(chat_id, "Invalid selection. Please choose a language from the options.")
            return {"ok": True}

    # ---------------- State 2: Awaiting Details (Name/Phone) ----------------
    if user_state.get('step') == 'awaiting_details':
        # Simple parsing: assume the whole message is the details.
        parts = [p.strip() for p in text.split(",", 1)]
        
        if not parts[0]:
            prompt = (
                "Please provide your name and WhatsApp number."
                if lang == "en" else
                "لطفاً نام و شماره واتساپ خود را وارد کنید."
                if lang == "fa" else
                "الرجاء إدخال الاسم ورقم واتساب."
                if lang == "ar" else
                "Пожалуйста, укажите ваше имя и номер WhatsApp."
            )
            await send_message(chat_id, prompt)
            return {"ok": True}

        # The user's name is the first part, phone is the second (optional)
        name_input = parts[0]
        phone_input = parts[1] if len(parts) > 1 else "Not provided"

        # Save details and move to main menu
        USER_STATE[chat_id]['name'] = name_input
        USER_STATE[chat_id]['phone'] = phone_input
        USER_STATE[chat_id]['step'] = 'main_menu' 
        
        welcome_msg = (
            f"Thank you, {name_input} 👋. Welcome to Taranteen online grocery.\n"
            "Please choose an option below:"
            if lang == "en" else
            f"ممنون، {name_input} 👋. به چت‌بات فروشگاه مواد غذایی تارانتین خوش آمدید.\n"
            "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:"
            if lang == "fa" else
            f"شكراً لك، {name_input} 👋. مرحباً بك في بقالة تارينتين عبر الإنترنت.\n"
            "الرجاء اختيار خيار أدناه:"
            if lang == "ar" else
            f"Спасибо, {name_input} 👋. Добро пожаловать в онлайн-магазин Taranteen.\n"
            "Пожалуйста, выберите один из вариантов ниже:"
        )

        await send_message(chat_id, welcome_msg, reply_markup=main_menu_keyboard(lang))
        return {"ok": True}


    # If not in one of the initial states, proceed with main menu logic
    if lang is None:
        # If the user somehow skipped the flow, ask them to start over
        await send_message(chat_id, "Please type /start to begin the conversation.")
        return {"ok": True}

    # ---------------- FA FLOWS (Main Menu) ----------------
    if lang == "fa":
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
                "۱. نام کامل (که قبلاً ثبت کردید)\n"
                "۲. نوع مشتری (خانواده / رستوران / سوپرمارکت و ...)\n"
                "۳. لیست اقلام درخواستی یا سؤالات شما\n"
                "۴. ایمیل یا شماره واتساپ (که قبلاً ثبت کردید)"
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


    # ---------------- AR FLOWS (Main Menu) ----------------
    elif lang == "ar":
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
                "1) الاسم الكامل (تم تسجيله مسبقاً)\n"
                "2) نوع العميل (عائلة / مطعم / سوبر ماركت / غير ذلك)\n"
                "3) قائمة الأصناف المطلوبة أو استفساراتك\n"
                "4) البريد الإلكتروني أو رقم واتساب (تم تسجيله مسبقاً)"
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
    
    # ---------------- RU FLOWS (Main Menu - NEW) ----------------
    elif lang == "ru":
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
                "1) Ваше полное имя (уже зарегистрировано)\n"
                "2) Тип клиента (семья / ресторан / супермаркет / другое)\n"
                "3) Список запрашиваемых товаров или ваши вопросы\n"
                "4) Электронная почта или номер WhatsApp (уже зарегистрированы)"
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

    # ---------------- EN FLOWS (Main Menu) ----------------
    elif lang == "en":
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
                "1) Your full name (already registered)\n"
                "2) Customer type (family / restaurant / supermarket / other)\n"
                "3) List of requested items or your questions\n"
                "4) Email or WhatsApp number (already registered)"
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
