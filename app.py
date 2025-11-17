import os
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Optional: catalog URLs (پر می‌کنی یا خالی می‌گذاری)
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
    else:
        return {
            "keyboard": [
                [{"text": "Products"}, {"text": "Offers & Discounts"}],
                [{"text": "Catalogs"}, {"text": "Delivery Areas & Times"}],
                [{"text": "Leave my details for order"}],
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
        }


def detect_lang(text: str) -> str:
    """Very naive language detection: if it sees Persian characters, returns fa."""
    for ch in text:
        if "\u0600" <= ch <= "\u06FF":
            return "fa"
    return "en"


def catalogs_message_en() -> str:
    return (
        "Here are Taranteen catalogs:\n\n"
        f"1) <a href=\"{CATALOG_1_URL}\">Catalog 1</a>\n"
        f"2) <a href=\"{CATALOG_2_URL}\">Catalog 2</a>\n"
        f"3) <a href=\"{CATALOG_3_URL}\">Catalog 3</a>\n"
        f"4) <a href=\"{CATALOG_4_URL}\">Catalog 4</a>\n"
        f"5) <a href=\"{CATALOG_5_URL}\">Catalog 5</a>\n"
        f"6) <a href=\"{CATALOG_6_URL}\">Catalog 6</a>\n\n"
        "In a real project, each link points to the latest PDF catalog of your products."
    )


def catalogs_message_fa() -> str:
    return (
        "کاتالوگ‌های فروشگاه مواد غذایی تارانتین:\n\n"
        f"۱) <a href=\"{CATALOG_1_URL}\">کاتالوگ ۱</a>\n"
        f"۲) <a href=\"{CATALOG_2_URL}\">کاتالوگ ۲</a>\n"
        f"۳) <a href=\"{CATALOG_3_URL}\">کاتالوگ ۳</a>\n"
        f"۴) <a href=\"{CATALOG_4_URL}\">کاتالوگ ۴</a>\n"
        f"۵) <a href=\"{CATALOG_5_URL}\">کاتالوگ ۵</a>\n"
        f"۶) <a href=\"{CATALOG_6_URL}\">کاتالوگ ۶</a>\n\n"
        "در نسخه واقعی، هر لینک به PDF به‌روز هر دسته از محصولات شما وصل می‌شود."
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

    lang = detect_lang(text)

    # ---------------- /start ----------------
    if text.startswith("/start"):
        greeting = (
            "Welcome to <b>Taranteen</b> 🛒\n"
            "Online grocery and food products.\n\n"
            "This bot helps you quickly see products, offers and catalogs, "
            "and leave your details for orders.\n\n"
            "Choose a language:\n"
            "• Type EN for English\n"
            "• یا بنویس FA برای فارسی\n"
        )
        await send_message(chat_id, greeting)
        return {"ok": True}

    # language selection
    if text.upper() == "EN":
        lang = "en"
    if text.upper() == "FA" or text == "فارسی":
        lang = "fa"

    # ---------------- FA FLOWS ----------------
    if lang == "fa":
        if text in ["FA", "فارسی"]:
            await send_message(
                chat_id,
                "به چت‌بات فروشگاه مواد غذایی تارانتین خوش آمدید 👋\n"
                "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:",
                reply_markup=main_menu_keyboard("fa"),
            )
            return {"ok": True}

        if text == "محصولات":
            msg = (
                "در تارانتین می‌تونید انواع مواد غذایی، محصولات تازه، کنسروی، نوشیدنی‌ها "
                "و اقلام روزمره خانه را سفارش بدهید.\n\n"
                "در نسخه کامل، این بخش می‌تواند لینک به دسته‌بندی‌ها در وب‌سایت یا "
                "لیست محصولات پرفروش باشد."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "تخفیف‌ها و پیشنهادها":
            msg = (
                "نمونه پیام تخفیف‌ها و پیشنهادهای ویژه تارانتین:\n\n"
                "• تخفیف هفتگی روی برخی اقلام پرمصرف\n"
                "• بسته‌های ترکیبی ویژه خانواده\n"
                "• پیشنهاد مخصوص رستوران‌ها و کافه‌ها\n\n"
                "در نسخه واقعی، این بخش هر هفته با آفرهای جدید به‌روزرسانی می‌شود."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "کاتالوگ‌ها":
            msg = catalogs_message_fa()
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "مناطق و زمان تحویل":
            msg = (
                "نمونه اطلاعات تحویل تارانتین:\n\n"
                "• ارسال در مناطق مشخص‌شده در دبی\n"
                "• بازه‌های زمانی تحویل (مثلاً صبح، بعدازظهر، شب)\n"
                "• امکان هماهنگی ارسال برای رستوران‌ها و فروشگاه‌ها\n\n"
                "در پروژه واقعی، این بخش دقیقاً بر اساس کسب‌وکار شما تنظیم می‌شود."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        if text == "ثبت اطلاعات برای سفارش":
            msg = (
                "برای اینکه تیم تارانتین بتواند با شما برای سفارش یا همکاری تماس بگیرد، "
                "لطفاً این اطلاعات را در یک پیام ارسال کنید:\n\n"
                "۱. نام\n"
                "۲. نوع مشتری (خانواده / رستوران / سوپرمارکت و ...)\n"
                "۳. ایمیل یا شماره واتساپ\n\n"
                "در نسخه واقعی، این اطلاعات به‌صورت سرنخ سفارش ذخیره می‌شود."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
            return {"ok": True}

        # any other FA text after that – treat as lead/demo
        msg = (
            "از پیام شما ممنونیم 🙏\n"
            "در نسخه واقعی، این پیام به‌عنوان سرنخ سفارش ذخیره و برای تیم فروش ارسال می‌شود.\n"
            "برای دیدن دوباره منو، از دکمه‌های پایین استفاده کنید."
        )
        await send_message(chat_id, msg, reply_markup=main_menu_keyboard("fa"))
        return {"ok": True}

    # ---------------- EN FLOWS ----------------
    if text.upper() == "EN" or lang == "en":
        if text.upper() == "EN":
            await send_message(
                chat_id,
                "Welcome to Taranteen online grocery 👋\n"
                "Please choose an option below:",
                reply_markup=main_menu_keyboard("en"),
            )
            return {"ok": True}

        if text == "Products":
            msg = (
                "Taranteen offers a wide range of grocery items: fresh products, pantry items, "
                "drinks and everyday essentials.\n\n"
                "In a full version, this section can link to categories on your website or show best-seller items."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Offers & Discounts":
            msg = (
                "Sample weekly offers from Taranteen:\n\n"
                "• Discounts on popular household items\n"
                "• Family bundle packs\n"
                "• Special offers for restaurants and cafés\n\n"
                "In the real project, this section would be updated weekly with live promotions."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Catalogs":
            msg = catalogs_message_en()
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Delivery Areas & Times":
            msg = (
                "Sample delivery information for Taranteen:\n\n"
                "• Delivery in defined areas in Dubai\n"
                "• Time slots (morning / afternoon / evening)\n"
                "• Special arrangements for restaurants and shops\n\n"
                "In the real project, this would show your exact delivery rules."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        if text == "Leave my details for order":
            msg = (
                "Please send your information in one message:\n\n"
                "1) Your name\n"
                "2) Customer type (family / restaurant / supermarket / other)\n"
                "3) Email or WhatsApp number\n\n"
                "In the real project, this data would be saved as an order lead and sent to your team."
            )
            await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
            return {"ok": True}

        # any other EN text after that – treat as lead/demo
        msg = (
            "Thank you for your message 🙏\n"
            "In the real project, this would be stored as a lead and forwarded to your team.\n"
            "Tap one of the buttons below to open the menu again."
        )
        await send_message(chat_id, msg, reply_markup=main_menu_keyboard("en"))
        return {"ok": True}

    return {"ok": True}
