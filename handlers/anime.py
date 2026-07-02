from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import (
    get_anime_by_code, get_anime_by_id, get_episode, get_episodes,
    add_history, add_favorite, remove_favorite, is_favorite,
    list_animes_with_ep_count, count_animes
)
from keyboards.main import (
    episodes_keyboard, no_episodes_keyboard,
    search_menu, catalog_keyboard
)

router = Router()

IGNORED_TEXTS = {
    "🔍 Anime Izlash", "🗂 Kabinet", "📱 Shorts", "📖 Qo'llanma", "📢 Reklama"
}


def format_anime_info(anime: dict, ep_count: int) -> str:
    status = anime.get("status", "Nomalum")
    total_ep = anime.get("total_episodes", 0)
    current_ep = anime.get("current_episode", 0)

    if status == "Tugallangan":
        ep_line = f"├‣ Anime: {total_ep} ta qism"
    else:
        ep_line = f"├‣ Anime: {current_ep}/{total_ep} qism"

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
    if anime.get("channel"):
        lines.append(f"├‣ Channel: {anime['channel']}")
    lines.append("╰──────────────────────")

    if ep_count > 0:
        lines.append(f"\n📺 <b>Qismni tanlang:</b> (jami {ep_count} ta yuklangan)")
    else:
        lines.append("\n⏳ <i>Qismlar hali yuklanmagan</i>")

    if anime.get("description"):
        lines.append(f"\n📄 {anime['description']}")
    return "\n".join(lines)


async def send_anime(message_or_callback, anime: dict, user_id: int, edit: bool = False):
    """Shared helper — sends or edits anime card with episode buttons."""
    episodes = await get_episodes(anime["id"])
    ep_count = len(episodes)
    is_fav = await is_favorite(user_id, anime["id"])
    caption = format_anime_info(anime, ep_count)
    kb = episodes_keyboard(anime["id"], episodes, is_fav) if episodes else no_episodes_keyboard(anime["id"], is_fav)

    await add_history(user_id, anime["id"])

    if edit:
        # called from callback — edit existing message
        try:
            await message_or_callback.edit_caption(caption=caption, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await message_or_callback.edit_text(caption, parse_mode="HTML", reply_markup=kb)
        return

    # called from message — send new
    if anime.get("thumbnail_file_id"):
        await message_or_callback.answer_photo(
            photo=anime["thumbnail_file_id"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await message_or_callback.answer(caption, parse_mode="HTML", reply_markup=kb)


# ─── SEARCH MENU ─────────────────────────────────────────────────────────────

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
        "✏️ Anime kodini yuboring (masalan: <code>AOT</code>):",
        parse_mode="HTML"
    )


# ─── CATALOG ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("catalog:") & ~F.data.startswith("catalog:view:"))
async def catalog_handler(callback: CallbackQuery):
    offset = int(callback.data.split(":")[1])
    animes = await list_animes_with_ep_count(offset=offset)
    total = await count_animes()

    if not animes:
        await callback.answer("📭 Hali anime qo'shilmagan!", show_alert=True)
        return

    page = offset // 8 + 1
    total_pages = (total + 7) // 8
    text = (
        f"📋 <b>Animeler katalogi</b> — {page}/{total_pages} sahifa\n"
        f"(jami {total} ta)\n\n"
        f"✅ — tugallangan  |  🔄 — davom etmoqda\n"
        f"Anime nomiga bosing va kodni yoki qismlarni ko'ring:"
    )

    kb = catalog_keyboard(animes, offset, total)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("catalog:view:"))
async def catalog_view_anime(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[2])
    anime = await get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True)
        return
    await send_anime(callback.message, anime, callback.from_user.id)
    await callback.answer()


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
    await send_anime(message, anime, message.from_user.id)


# ─── EPISODE DOWNLOAD ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ep:"))
async def episode_download(callback: CallbackQuery):
    _, anime_id, ep_num = callback.data.split(":")
    anime_id, ep_num = int(anime_id), int(ep_num)

    episode = await get_episode(anime_id, ep_num)
    if not episode or not episode.get("file_id"):
        await callback.answer("❌ Fayl topilmadi!", show_alert=True)
        return

    anime = await get_anime_by_id(anime_id)
    await callback.answer(f"📦 {ep_num}-qism yuborilmoqda...")
    await callback.message.answer_document(
        document=episode["file_id"],
        caption=(
            f"🎬 <b>{anime['name']}</b>\n"
            f"📺 {ep_num}-qism"
            f"{' — ' + episode['title'] if episode.get('title') else ''}\n"
            f"📌 Kod: <code>{anime['code']}</code>"
        ),
        parse_mode="HTML",
    )


# ─── FAVORITES ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fav:"))
async def favorite_handler(callback: CallbackQuery):
    anime_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    episodes = await get_episodes(anime_id)

    if await is_favorite(user_id, anime_id):
        await remove_favorite(user_id, anime_id)
        await callback.answer("💔 Sevimlilardan olib tashlandi")
        is_fav = False
    else:
        await add_favorite(user_id, anime_id)
        await callback.answer("❤️ Sevimlilarga qo'shildi!")
        is_fav = True

    new_kb = (
        episodes_keyboard(anime_id, episodes, is_fav)
        if episodes else no_episodes_keyboard(anime_id, is_fav)
    )
    await callback.message.edit_reply_markup(reply_markup=new_kb)
