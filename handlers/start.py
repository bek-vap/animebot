from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from database.db import register_user
from keyboards.main import main_menu, cabinet_menu

router = Router()

WELCOME_GIF = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcWd5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5ZzZ5Zz/giphy.gif"

WELCOME_TEXT = (
    "👋 <b>Assalomu aleykum botimizga xush kelibsiz.</b>\n\n"
    "🔸 Botimizda animelarni kanalimizga kirib yuklab olib, tomosha qilishingiz mumkin.\n\n"
    "‼️ Botga to'g'ri kodni yuborishingiz mumkin!"
)


@router.message(CommandStart())
async def start_handler(message: Message):
    await register_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )
    try:
        await message.answer_animation(
            animation=WELCOME_GIF,
            caption=WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )
    except Exception:
        await message.answer(
            text=WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


@router.message(F.text == "📖 Qo'llanma")
async def guide_handler(message: Message):
    text = (
        "📖 <b>Qo'llanma</b>\n\n"
        "1️⃣ Anime kodini yozing (masalan: <code>AOT01</code>)\n"
        "2️⃣ Bot sizga animeni ma'lumotlari bilan birga yuboradi\n"
        "3️⃣ <b>Yuklab olish</b> tugmasini bosib faylni oling\n\n"
        "📌 Kodlarni kanalimizdan topishingiz mumkin!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📢 Reklama")
async def ads_handler(message: Message):
    text = (
        "📢 <b>Reklama</b>\n\n"
        "Reklamani joylashtirish uchun admin bilan bog'laning:\n"
        "👤 @admin_username\n\n"
        "💰 Narxlar va shartlar admin bilan kelishiladi."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📱 Shorts")
async def shorts_handler(message: Message):
    await message.answer(
        "📱 <b>Shorts</b> bo'limi tez orada ishga tushadi!",
        parse_mode="HTML"
    )
