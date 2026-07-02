from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import get_user_history, get_favorites
from keyboards.main import cabinet_menu, main_menu

router = Router()


@router.message(F.text == "🗂 Kabinet")
async def cabinet_handler(message: Message):
    text = (
        f"🗂 <b>Kabinet</b>\n\n"
        f"👤 <b>{message.from_user.full_name}</b>\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"🔗 Username: @{message.from_user.username or 'yo\'q'}\n\n"
        f"Nima ko'rishni xohlaysiz?"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=cabinet_menu())


@router.callback_query(F.data == "cabinet:history")
async def history_handler(callback: CallbackQuery):
    history = await get_user_history(callback.from_user.id)
    if not history:
        await callback.answer("📜 Ko'rish tarixi bo'sh", show_alert=True)
        return

    lines = ["📜 <b>So'nggi ko'rilgan animeler:</b>\n"]
    for i, item in enumerate(history, 1):
        lines.append(f"{i}. <b>{item['name']}</b> — <code>{item['code']}</code>")

    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=cabinet_menu())


@router.callback_query(F.data == "cabinet:favorites")
async def favorites_handler(callback: CallbackQuery):
    favs = await get_favorites(callback.from_user.id)
    if not favs:
        await callback.answer("❤️ Sevimlilar bo'sh", show_alert=True)
        return

    lines = ["❤️ <b>Sevimli animelerim:</b>\n"]
    for i, item in enumerate(favs, 1):
        lines.append(f"{i}. <b>{item['name']}</b> — <code>{item['code']}</code>")

    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=cabinet_menu())


@router.callback_query(F.data == "cabinet:back")
async def cabinet_back(callback: CallbackQuery):
    await callback.message.delete()
