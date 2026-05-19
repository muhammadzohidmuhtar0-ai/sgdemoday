import asyncio
import json
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from dotenv import load_dotenv

import sheets

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@Startupgarage_uz")


def _parse_admin_group(value: str | None):
    if not value:
        return None
    value = value.strip()
    if value.lstrip("-").isdigit():
        return int(value)
    return value


ADMIN_GROUP_ID = _parse_admin_group(os.getenv("ADMIN_GROUP_ID"))
SKIP_SUBSCRIPTION_CHECK = os.getenv("SKIP_SUBSCRIPTION_CHECK", "0") == "1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

USER_MAP_FILE = Path(__file__).parent / "user_map.json"
admin_group_chat_id: int | None = None


def _load_user_map() -> dict:
    try:
        return json.loads(USER_MAP_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_user_map(m: dict) -> None:
    USER_MAP_FILE.write_text(json.dumps(m))


def _remember(message_id: int, user_id: int) -> None:
    m = _load_user_map()
    m[str(message_id)] = user_id
    _save_user_map(m)


class Form(StatesGroup):
    full_name = State()
    startup_name = State()
    phone = State()
    file = State()


def subscribe_kb() -> InlineKeyboardMarkup:
    channel_link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=channel_link)],
            [InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="check_sub")],
        ]
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    if SKIP_SUBSCRIPTION_CHECK:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramBadRequest as e:
        logger.warning("Subscription check failed: %s", e)
        return False


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if await is_subscribed(bot, message.from_user.id):
        await start_application(message, state)
        return
    await message.answer(
        f"Assalomu alaykum! 👋\n\n"
        f"Startup Garage Demo Day'ga ariza topshirish uchun, "
        f"avval rasmiy kanalimizga obuna bo'ling: {CHANNEL_USERNAME}\n\n"
        f"Obuna bo'lgach, pastdagi tugmani bosing.",
        reply_markup=subscribe_kb(),
    )


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if await is_subscribed(bot, callback.from_user.id):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer("Obuna tasdiqlandi ✅")
        await start_application(callback.message, state, user=callback.from_user)
    else:
        await callback.answer(
            "Siz hali kanalga obuna bo'lmadingiz. Iltimos, obuna bo'ling va qaytadan urinib ko'ring.",
            show_alert=True,
        )


async def start_application(message: Message, state: FSMContext, user=None):
    await state.set_state(Form.full_name)
    await message.answer(
        "Ajoyib! Endi arizani to'ldiramiz.\n\n"
        "1️⃣ <b>Ism Familiyangizni</b> kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Form.full_name, F.text)
async def get_full_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 3:
        await message.answer("Iltimos, to'liq ism familiyangizni kiriting.")
        return
    await state.update_data(full_name=text)
    await state.set_state(Form.startup_name)
    await message.answer("2️⃣ <b>Startup nomini</b> kiriting:")


@router.message(Form.startup_name, F.text)
async def get_startup_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 2:
        await message.answer("Iltimos, startup nomini to'g'ri kiriting.")
        return
    await state.update_data(startup_name=text)
    await state.set_state(Form.phone)
    await message.answer(
        "3️⃣ <b>Telefon raqamingizni</b> yuboring.\n\n"
        "Pastdagi tugmani bosib, Telegram orqali raqamingizni yuboring 👇",
        reply_markup=phone_kb(),
    )


@router.message(Form.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        await message.answer("Iltimos, faqat o'zingizning raqamingizni yuboring.")
        return
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(Form.file)
    await message.answer(
        "4️⃣ <b>Loyiha faylingizni</b> (pitch deck, taqdimot, hujjat yoki rasm) yuboring.\n\n"
        "Hujjat (PDF, DOCX, PPTX...) yoki rasm — istalgan formatda qabul qilinadi.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Form.phone)
async def phone_invalid(message: Message):
    await message.answer(
        "Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring 👇",
        reply_markup=phone_kb(),
    )


@router.message(Form.file, F.document | F.photo)
async def get_file(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "fayl"
        is_photo = False
    else:
        file_id = message.photo[-1].file_id
        file_name = "rasm.jpg"
        is_photo = True

    payload = {
        "user_id": message.from_user.id,
        "username": message.from_user.username or "",
        "full_name": data.get("full_name", ""),
        "startup_name": data.get("startup_name", ""),
        "phone": data.get("phone", ""),
        "file_name": file_name,
        "file_link": "",
    }

    try:
        admin_text = (
            "🆕 <b>Yangi ariza</b>\n\n"
            f"👤 <b>Ism:</b> {payload['full_name']}\n"
            f"🚀 <b>Startup:</b> {payload['startup_name']}\n"
            f"📞 <b>Telefon:</b> {payload['phone']}\n"
            f"🆔 <b>Telegram:</b> @{payload['username'] or '—'} "
            f"(<code>{payload['user_id']}</code>)\n\n"
            "💬 <i>Bu xabarga reply qilib javob yozsangiz — foydalanuvchiga yuboriladi.</i>"
        )
        sent_msg = await bot.send_message(ADMIN_GROUP_ID, admin_text)
        caption = f"📎 {payload['full_name']} — {payload['startup_name']}"
        if is_photo:
            sent = await bot.send_photo(ADMIN_GROUP_ID, file_id, caption=caption)
        else:
            sent = await bot.send_document(ADMIN_GROUP_ID, file_id, caption=caption)
        _remember(sent_msg.message_id, payload["user_id"])
        _remember(sent.message_id, payload["user_id"])
        if sent.chat.username:
            payload["file_link"] = f"https://t.me/{sent.chat.username}/{sent.message_id}"
        else:
            chat_id_str = str(sent.chat.id).replace("-100", "", 1)
            payload["file_link"] = f"https://t.me/c/{chat_id_str}/{sent.message_id}"
    except Exception as e:
        logger.exception("Admin group send error: %s", e)

    try:
        await asyncio.to_thread(sheets.append_application, payload)
    except Exception as e:
        logger.exception("Google Sheets error: %s", e)

    await state.clear()
    await message.answer(
        "✅ <b>Loyihangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        "2 ish kuni ichida sizga saralash javoblarini jo'natamiz.\n\n"
        "Startup Garage jamoasi 🚀"
    )


@router.message(Form.file)
async def file_invalid(message: Message):
    await message.answer("Iltimos, hujjat (document) yoki rasm yuboring.")


@router.message(F.reply_to_message)
async def relay_admin_reply(message: Message, bot: Bot):
    if admin_group_chat_id is None or message.chat.id != admin_group_chat_id:
        return
    target_user_id = _load_user_map().get(str(message.reply_to_message.message_id))
    if not target_user_id:
        return
    try:
        await bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        await message.reply("✅ Foydalanuvchiga yuborildi", disable_notification=True)
    except Exception as e:
        logger.exception("Relay error: %s", e)
        await message.reply(f"❌ Yuborib bo'lmadi: {e}", disable_notification=True)


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN .env faylida ko'rsatilmagan!")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    global admin_group_chat_id
    try:
        chat = await bot.get_chat(ADMIN_GROUP_ID)
        admin_group_chat_id = chat.id
        logger.info("Admin group: %s (id=%s)", chat.title, admin_group_chat_id)
    except Exception as e:
        logger.exception("Admin group resolve error: %s", e)

    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
