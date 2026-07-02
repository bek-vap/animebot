from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import (
    get_anime_by_code, get_anime_by_id,
    add_history, add_favorite, remove_favorite, is_favorite,
    list_animes, count_animes,
)
from keyboards.main import anime_actions, search_menu, catalog_keyboard
from config import SOURCE_CHANNEL_ID

router = Router()

IGNORED_TEXTS = {
    "🔍 Anime Izlash", "🗂 Kabinet", "📱 Shorts", "📖 Qo'llanma", "📢 Reklama"
}


def format_anime_card(anime: dict) -> str:
    status = anime.get("status", "Nomalum")
    total_ep = anime.get("total_episodes", 0)
    current_ep = anime.get("current_episode", 0)
    ep_line = f"├‣ Anime: {total_ep} ta qism" if status == "Tugallangan" else f"├‣ Anime: {current_ep}/{total_ep} qism"

    lines = [
        f"<b>{anime['name']}</b>",
        "╭──────────────────────",
        f"├‣ Status: {status}",
        ep_line,
    ]
    if anime.get("translation"):
        lines.append(f"├‣ Translation: {anime['translation']}")
    if anime.get("genres"):
        lines.append(f"├‣ Genres: {anime['genres']}")
    lines.append("╰──────────────────────")
    if anime.get("description"):
        lines.append(f"\n📄 {anime['description']}")
    return "\n".join(lines)


async def deliver_anime(message: Message, anime: dict):
    """Send anime card then forward video from source channel."""
    user_id = message.from_user.id
    is_fav = await is_favorite(user_id, anime["id"])
    caption = format_anime_card(anime)
    kb = anime_actions(anime["id"], is_fav)

    await add_history(user_id, anime["id"])

    # Send info card
    if anime.get("thumbnail_file_id"):
        await message.answer_photo(photo=anime["thumbnail_file_id"], caption=caption,
                                   parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(caption, parse_mode="HTML", reply_markup=kb)

    # Forward video from source channel
    msg_id = anime.get("source_message_id", 0)
    import logging
    log = logging.getLogger(__name__)
    log.info(f"[ANIME] code={anime['code']} source_message_id={msg_id} SOURCE_CHANNEL_ID={SOURCE_CHANNEL_ID!r}")

    if msg_id and SOURCE_CHANNEL_ID:
        try:
            await message.bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=SOURCE_CHANNEL_ID,
                message_id=msg_id,
                caption=" ",
                parse_mode=None,
            )
            log.info(f"[ANIME] copy OK: msg_id={msg_id} -> chat_id={message.chat.id}")
        except Exception as e:
            log.error(f"[ANIME] forward FAILED: {e}")
            await message.answer(
                f"⚠️ <b>Video yuborishda xato!</b>\n<code>{e}</code>",
                parse_mode="HTML"
            )
    elif not SOURCE_CHANNEL_ID:
        log.warning("[ANIME] SOURCE_CHANNEL_ID is not set in .env")
        await message.answer("⚠️ SOURCE_CHANNEL_ID sozlanmagan!", parse_mode="HTML")
    else:
        log.warning(f"[ANIME] source_message_id=0 for code={anime['code']}")
        await message.answer(
            "⏳ <b>Video hali kanalga yuklanmagan.</b>\n"
            f"Kanalda <code>Anime codi: {anime['code']}</code> caption bilan post qo'shilgach avtomatik topiladi.",
            parse_mode="HTML"
        )


# ─── SEARCH ──────────────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Anime Izlash")
async def search_handler(message: Message):
    total = await count_animes()
    await message.answer(
        f"🔍 <b>Anime qidirish</b>\n\n"
        f"📚 Bazada jami <b>{total}</b> ta anime mavjud.\n\n"
        f"Kod bilsangiz — to'g'ridan-to'g'ri yuboring.\n"
        f"Bilmasangiz — katalogdan tanlang:",
        parse_mode="HTML",
        reply_markup=search_menu()
    )


@router.callback_query(F.data == "search:bycode")
async def search_by_code_hint(callback: CallbackQuery):
    await callback.message.edit_text(
        "✏️ Anime kodini yuboring (masalan: <code>81</code>):",
        parse_mode="HTML"
    )


# ─── CATALOG ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("catalog:") & ~F.data.startswith("catalog:view:"))
async def catalog_handler(callback: CallbackQuery):
    offset = int(callback.data.split(":")[1])
    animes = await list_animes(offset=offset)
    total = await count_animes()
    if not animes:
        await callback.answer("📭 Hali anime qo'shilmagan!", show_alert=True)
        return
    page = offset // 8 + 1
    total_pages = (total + 7) // 8
    text = (
        f"📋 <b>Animeler katalogi</b> — {page}/{total_pages} sahifa (jami {total} ta)\n\n"
        f"✅ — tugallangan  |  🔄 — davom etmoqda"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=catalog_keyboard(animes, offset, total))
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=catalog_keyboard(animes, offset, total))


@router.callback_query(F.data.startswith("catalog:view:"))
async def catalog_view_anime(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[2])
    anime = await get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await callback.answer()
    await deliver_anime(callback.message, anime)


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    await callback.answer()


# ─── CODE INPUT ──────────────────────────────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(IGNORED_TEXTS))
async def code_handler(message: Message):
    code = message.text.strip()
    anime = await get_anime_by_code(code)
    if not anime:
        await message.answer(
            "❌ <b>Bunday kodli anime topilmadi!</b>\n\n"
            "📌 Kodni to'g'ri yozganingizni tekshiring yoki katalogdan qidiring.",
            parse_mode="HTML",
            reply_markup=search_menu()
        )
        return
    await deliver_anime(message, anime)


# ─── FAVORITES ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fav:"))
async def favorite_handler(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    if await is_favorite(user_id, anime_id):
        await remove_favorite(user_id, anime_id)
        await callback.answer("💔 Sevimlilardan olib tashlandi")
        is_fav = False
    else:
        await add_favorite(user_id, anime_id)
        await callback.answer("❤️ Sevimlilarga qo'shildi!")
        is_fav = True
    await callback.message.edit_reply_markup(reply_markup=anime_actions(anime_id, is_fav))
