from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import ADMIN_IDS, ADMIN_PASSWORD
from database.db import (
    add_anime, delete_anime, update_anime, list_animes,
    count_animes, count_users, get_anime_by_code, get_anime_by_id,
    is_admin_in_db, add_admin, remove_admin, list_admins,
    add_episode, update_episode, delete_episode, get_episodes,
    get_episode, count_episodes
)
from keyboards.main import (
    admin_menu, admin_anime_list, admin_anime_detail,
    admin_edit_fields, confirm_delete,
    admin_episodes_list, admin_episode_detail, confirm_delete_ep
)
import aiosqlite
from database.db import DB_PATH

router = Router()


class PasswordState(StatesGroup):
    waiting = State()


class AddAnime(StatesGroup):
    code = State()
    name = State()
    status = State()
    total_episodes = State()
    current_episode = State()
    translation = State()
    genres = State()
    channel = State()
    thumbnail = State()
    description = State()


class AddEpisode(StatesGroup):
    number = State()
    title = State()
    file = State()


class ReplaceEpisodeFile(StatesGroup):
    file = State()


class EditField(StatesGroup):
    waiting = State()


async def check_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or await is_admin_in_db(user_id)


# ─── /panel ──────────────────────────────────────────────────────────────────

@router.message(Command("panel"))
async def panel_handler(message: Message, state: FSMContext):
    if await check_admin(message.from_user.id):
        await message.answer("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_menu())
        return
    await state.set_state(PasswordState.waiting)
    await message.answer(
        "🔐 <b>Admin paneliga kirish</b>\n\nParolni kiriting:",
        parse_mode="HTML"
    )


@router.message(PasswordState.waiting)
async def password_check(message: Message, state: FSMContext):
    await message.delete()
    if message.text.strip() == ADMIN_PASSWORD:
        await add_admin(
            user_id=message.from_user.id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name or "",
        )
        await state.clear()
        await message.answer(
            "✅ <b>Parol to'g'ri! Siz admin bo'ldingiz.</b>",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )
    else:
        await state.clear()
        await message.answer("❌ <b>Parol noto'g'ri!</b>", parse_mode="HTML")


# ─── PANEL CALLBACKS ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    await callback.message.edit_text("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_menu())


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    users = await count_users()
    animes = await count_animes()
    admins = await list_admins()
    admin_list = "\n".join(
        f"  • {a['full_name']} (@{a['username'] or 'yo\'q'})" for a in admins
    ) or "  — yo'q"
    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Animeler: <b>{animes}</b>\n\n"
        f"👑 Adminlar:\n{admin_list}"
    )
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🔙 Panel", callback_data="admin:back"))
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("admin:list:"))
async def admin_list_handler(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    offset = int(callback.data.split(":")[2])
    animes = await list_animes(offset=offset)
    total = await count_animes()
    if not animes:
        await callback.answer("📋 Animeler yo'q", show_alert=True)
        return
    await callback.message.edit_text(
        f"📋 <b>Animeler ro'yxati</b> (jami: {total})",
        parse_mode="HTML",
        reply_markup=admin_anime_list(animes, offset, total)
    )


@router.callback_query(F.data.startswith("admin:anime:"))
async def admin_anime_detail_handler(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    anime_id = int(callback.data.split(":")[2])
    anime = await get_anime_by_id(anime_id)
    if not anime:
        await callback.answer("Topilmadi", show_alert=True)
        return
    ep_count = await count_episodes(anime_id)
    text = (
        f"🎬 <b>{anime['name']}</b>\n"
        f"🔑 Kod: <code>{anime['code']}</code>\n"
        f"📊 Status: {anime['status']}\n"
        f"📺 Qismlar: {anime['current_episode']}/{anime['total_episodes']} (yuklangan: {ep_count})\n"
        f"🌐 Tarjima: {anime['translation']}\n"
        f"🎭 Janrlar: {anime['genres']}\n"
        f"📢 Kanal: {anime['channel']}\n"
        f"🖼 Muqova: {'✅' if anime['thumbnail_file_id'] else '❌'}"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=admin_anime_detail(anime_id, ep_count)
    )


# ─── EPISODE MANAGEMENT ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:eps:"))
async def admin_episodes_handler(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    anime_id = int(callback.data.split(":")[2])
    anime = await get_anime_by_id(anime_id)
    episodes = await get_episodes(anime_id)
    if not episodes:
        await callback.answer("📺 Hali qism qo'shilmagan", show_alert=True)
        return
    await callback.message.edit_text(
        f"📺 <b>{anime['name']}</b> — qismlar:",
        parse_mode="HTML",
        reply_markup=admin_episodes_list(anime_id, episodes)
    )


@router.callback_query(F.data.startswith("admin:ep:"))
async def admin_episode_detail_handler(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    anime_id, ep_num = int(parts[2]), int(parts[3])
    anime = await get_anime_by_id(anime_id)
    ep = await get_episode(anime_id, ep_num)
    if not ep:
        await callback.answer("Topilmadi", show_alert=True)
        return
    title = ep.get("title") or "—"
    text = (
        f"📺 <b>{anime['name']}</b>\n"
        f"🔢 {ep_num}-qism\n"
        f"📝 Sarlavha: {title}\n"
        f"📁 Fayl: ✅"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=admin_episode_detail(anime_id, ep_num)
    )


@router.callback_query(F.data.startswith("admin:addep:"))
async def admin_add_ep_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    anime_id = int(callback.data.split(":")[2])
    anime = await get_anime_by_id(anime_id)
    episodes = await get_episodes(anime_id)
    next_num = (episodes[-1]["episode_number"] + 1) if episodes else 1

    await state.set_state(AddEpisode.number)
    await state.update_data(anime_id=anime_id)
    await callback.message.answer(
        f"➕ <b>{anime['name']}</b> uchun yangi qism\n\n"
        f"📺 Qism raqamini kiriting (tavsiya: <code>{next_num}</code>):",
        parse_mode="HTML"
    )


@router.message(AddEpisode.number)
async def add_ep_number(message: Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!")
        return

    data = await state.get_data()
    existing = await get_episode(data["anime_id"], num)
    if existing:
        await message.answer(f"⚠️ {num}-qism allaqachon mavjud! Boshqa raqam kiriting:")
        return

    await state.update_data(episode_number=num)
    await state.set_state(AddEpisode.title)
    await message.answer("📝 Qism sarlavhasini kiriting (yoki /skip):")


@router.message(AddEpisode.title)
async def add_ep_title(message: Message, state: FSMContext):
    title = "" if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(title=title)
    await state.set_state(AddEpisode.file)
    await message.answer("📁 Qism faylini yuboring (video yoki hujjat):")


@router.message(AddEpisode.file, F.video | F.document)
async def add_ep_file(message: Message, state: FSMContext):
    file_id = message.video.file_id if message.video else message.document.file_id
    data = await state.get_data()
    await state.clear()

    success = await add_episode(
        anime_id=data["anime_id"],
        episode_number=data["episode_number"],
        file_id=file_id,
        title=data.get("title", "")
    )
    anime = await get_anime_by_id(data["anime_id"])
    ep_count = await count_episodes(data["anime_id"])

    if success:
        await message.answer(
            f"✅ <b>{data['episode_number']}-qism qo'shildi!</b>\n"
            f"🎬 {anime['name']}\n"
            f"📺 Jami yuklangan: {ep_count} ta qism",
            parse_mode="HTML",
            reply_markup=admin_anime_detail(data["anime_id"], ep_count)
        )
    else:
        await message.answer("❌ Qo'shishda xato yuz berdi.")


@router.callback_query(F.data.startswith("admin:delep:"))
async def admin_delete_ep_confirm(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    anime_id, ep_num = int(parts[2]), int(parts[3])
    await callback.message.edit_text(
        f"🗑 <b>{ep_num}-qismni o'chirmoqchimisiz?</b>",
        parse_mode="HTML",
        reply_markup=confirm_delete_ep(anime_id, ep_num)
    )


@router.callback_query(F.data.startswith("admin:confirmdelep:"))
async def admin_do_delete_ep(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    anime_id, ep_num = int(parts[2]), int(parts[3])
    await delete_episode(anime_id, ep_num)
    episodes = await get_episodes(anime_id)
    await callback.message.edit_text(
        f"✅ {ep_num}-qism o'chirildi!",
        reply_markup=admin_episodes_list(anime_id, episodes) if episodes else None
    )


@router.callback_query(F.data.startswith("admin:epfile:"))
async def admin_replace_ep_file(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    anime_id, ep_num = int(parts[2]), int(parts[3])
    await state.set_state(ReplaceEpisodeFile.file)
    await state.update_data(anime_id=anime_id, episode_number=ep_num)
    await callback.message.answer(
        f"📁 {ep_num}-qism uchun yangi faylni yuboring:",
        parse_mode="HTML"
    )


@router.message(ReplaceEpisodeFile.file, F.video | F.document)
async def replace_ep_file_save(message: Message, state: FSMContext):
    file_id = message.video.file_id if message.video else message.document.file_id
    data = await state.get_data()
    await state.clear()
    ep = await get_episode(data["anime_id"], data["episode_number"])
    await update_episode(
        anime_id=data["anime_id"],
        episode_number=data["episode_number"],
        file_id=file_id,
        title=ep.get("title", "") if ep else ""
    )
    await message.answer(
        f"✅ {data['episode_number']}-qism fayli yangilandi!",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


# ─── DELETE ANIME ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:delete:"))
async def admin_delete_confirm(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    anime_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "🗑 <b>Rostdan ham o'chirmoqchimisiz?\nBarcha qismlar ham o'chib ketadi!</b>",
        parse_mode="HTML",
        reply_markup=confirm_delete(anime_id)
    )


@router.callback_query(F.data.startswith("admin:confirmdelete:"))
async def admin_do_delete(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    anime_id = int(callback.data.split(":")[2])
    await delete_anime(anime_id)
    await callback.message.edit_text("✅ Anime va barcha qismlari o'chirildi!", reply_markup=None)


# ─── ADD ANIME FSM ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:add")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    await state.set_state(AddAnime.code)
    await callback.message.answer("🔑 Anime kodini kiriting (masalan: <code>AOT</code>):", parse_mode="HTML")


@router.message(AddAnime.code)
async def add_code(message: Message, state: FSMContext):
    existing = await get_anime_by_code(message.text.strip())
    if existing:
        await message.answer("❌ Bu kod allaqachon mavjud! Boshqa kod kiriting:")
        return
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AddAnime.name)
    await message.answer("📝 Anime nomini kiriting:")


@router.message(AddAnime.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddAnime.status)
    await message.answer("📊 Status:\n<code>Tugallangan</code> yoki <code>Davom etmoqda</code>", parse_mode="HTML")


@router.message(AddAnime.status)
async def add_status(message: Message, state: FSMContext):
    await state.update_data(status=message.text.strip())
    await state.set_state(AddAnime.total_episodes)
    await message.answer("🎬 Jami qismlar sonini kiriting:")


@router.message(AddAnime.total_episodes)
async def add_total_ep(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting!")
        return
    await state.update_data(total_episodes=val)
    await state.set_state(AddAnime.current_episode)
    await message.answer("📺 Joriy qism sonini kiriting (0 bo'lsa 0 yozing):")


@router.message(AddAnime.current_episode)
async def add_current_ep(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting!")
        return
    await state.update_data(current_episode=val)
    await state.set_state(AddAnime.translation)
    await message.answer("🌐 Tarjima nomini kiriting:")


@router.message(AddAnime.translation)
async def add_translation(message: Message, state: FSMContext):
    await state.update_data(translation=message.text.strip())
    await state.set_state(AddAnime.genres)
    await message.answer("🎭 Janrlarni kiriting (masalan: Action, Drama):")


@router.message(AddAnime.genres)
async def add_genres(message: Message, state: FSMContext):
    await state.update_data(genres=message.text.strip())
    await state.set_state(AddAnime.channel)
    await message.answer("📢 Kanal username kiriting (masalan: @AnimAfundub):")


@router.message(AddAnime.channel)
async def add_channel(message: Message, state: FSMContext):
    await state.update_data(channel=message.text.strip())
    await state.set_state(AddAnime.thumbnail)
    await message.answer("🖼 Muqova rasmini yuboring (yoki /skip):")


@router.message(AddAnime.thumbnail, F.photo)
async def add_thumbnail_photo(message: Message, state: FSMContext):
    await state.update_data(thumbnail_file_id=message.photo[-1].file_id)
    await state.set_state(AddAnime.description)
    await message.answer("📄 Qisqacha tavsif kiriting (yoki /skip):")


@router.message(AddAnime.thumbnail, F.text == "/skip")
async def add_thumbnail_skip(message: Message, state: FSMContext):
    await state.update_data(thumbnail_file_id="")
    await state.set_state(AddAnime.description)
    await message.answer("📄 Qisqacha tavsif kiriting (yoki /skip):")


@router.message(AddAnime.description)
async def add_description(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(description=desc)
    data = await state.get_data()
    await state.clear()

    anime_id = await add_anime(data)
    await message.answer(
        f"✅ <b>Anime qo'shildi!</b>\n\n"
        f"🎬 Nom: {data['name']}\n"
        f"🔑 Kod: <code>{data['code']}</code>\n\n"
        f"➡️ Endi qismlarni qo'shing:",
        parse_mode="HTML",
        reply_markup=admin_anime_detail(anime_id, 0)
    )


# ─── EDIT FIELD FSM ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:edit:"))
async def admin_edit_menu(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        return
    anime_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "✏️ <b>Qaysi maydonni tahrirlaysiz?</b>",
        parse_mode="HTML",
        reply_markup=admin_edit_fields(anime_id)
    )


@router.callback_query(F.data.startswith("admin:editfield:"))
async def admin_edit_field_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    anime_id, field = int(parts[2]), parts[3]
    await state.set_state(EditField.waiting)
    await state.update_data(anime_id=anime_id, field=field)
    if field == "thumbnail_file_id":
        await callback.message.answer("🖼 Yangi muqova rasmini yuboring:")
    else:
        await callback.message.answer(f"✏️ Yangi qiymat kiriting (<code>{field}</code>):", parse_mode="HTML")


@router.message(EditField.waiting)
async def admin_edit_field_save(message: Message, state: FSMContext):
    data = await state.get_data()
    field, anime_id = data["field"], data["anime_id"]

    if field == "thumbnail_file_id" and message.photo:
        value = message.photo[-1].file_id
    elif field in {"total_episodes", "current_episode"}:
        try:
            value = int(message.text.strip())
        except ValueError:
            await message.answer("❌ Raqam kiriting!")
            return
    else:
        value = message.text.strip()

    await update_anime(anime_id, {field: value})
    await state.clear()
    await message.answer(f"✅ <b>{field}</b> yangilandi!", parse_mode="HTML", reply_markup=admin_menu())
