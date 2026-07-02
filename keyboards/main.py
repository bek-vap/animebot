from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def search_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Barcha animeler katalogi", callback_data="catalog:0"))
    builder.row(InlineKeyboardButton(text="✏️ Kod orqali izlash", callback_data="search:bycode"))
    return builder.as_markup()


def catalog_keyboard(animes: list, offset: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for anime in animes:
        ep_count = anime.get("ep_count", 0)
        status_icon = "✅" if anime["status"] == "Tugallangan" else "🔄"
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {anime['name']} [{anime['code']}] ({ep_count} qism)",
            callback_data=f"catalog:view:{anime['id']}"
        ))

    nav = []
    page = offset // 8 + 1
    total_pages = (total + 7) // 8
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"catalog:{offset - 8}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if offset + 8 < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"catalog:{offset + 8}"))
    if nav:
        builder.row(*nav)
    return builder.as_markup()


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔍 Anime Izlash"))
    builder.row(
        KeyboardButton(text="🗂 Kabinet"),
        KeyboardButton(text="📱 Shorts"),
    )
    builder.row(
        KeyboardButton(text="📖 Qo'llanma"),
        KeyboardButton(text="📢 Reklama"),
    )
    return builder.as_markup(resize_keyboard=True)


def episodes_keyboard(anime_id: int, episodes: list, is_fav: bool) -> InlineKeyboardMarkup:
    """Episode buttons — 5 per row, max 50 episodes shown."""
    builder = InlineKeyboardBuilder()
    row = []
    for ep in episodes[:50]:
        num = ep["episode_number"]
        title = ep.get("title", "")
        label = f"{num}" if not title else f"{num}. {title[:12]}"
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"ep:{anime_id}:{num}"
        ))
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    fav_text = "❤️ Sevimlilardan olib tashlash" if is_fav else "🤍 Sevimlilarga qo'shish"
    builder.row(InlineKeyboardButton(text=fav_text, callback_data=f"fav:{anime_id}"))
    return builder.as_markup()


def no_episodes_keyboard(anime_id: int, is_fav: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fav_text = "❤️ Sevimlilardan olib tashlash" if is_fav else "🤍 Sevimlilarga qo'shish"
    builder.row(InlineKeyboardButton(text=fav_text, callback_data=f"fav:{anime_id}"))
    return builder.as_markup()


def cabinet_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📜 Ko'rish tarixi", callback_data="cabinet:history"))
    builder.row(InlineKeyboardButton(text="❤️ Sevimlilar", callback_data="cabinet:favorites"))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="cabinet:back"))
    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Anime qo'shish", callback_data="admin:add"))
    builder.row(InlineKeyboardButton(text="📋 Animeler ro'yxati", callback_data="admin:list:0"))
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"))
    return builder.as_markup()


def admin_anime_list(animes: list, offset: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for anime in animes:
        builder.row(InlineKeyboardButton(
            text=f"🎬 {anime['name']} [{anime['code']}]",
            callback_data=f"admin:anime:{anime['id']}"
        ))
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin:list:{offset - 10}"))
    if offset + 10 < total:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin:list:{offset + 10}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Panel", callback_data="admin:back"))
    return builder.as_markup()


def admin_anime_detail(anime_id: int, ep_count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"➕ Qism qo'shish (hozir: {ep_count} ta)",
        callback_data=f"admin:addep:{anime_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="🗂 Qismlarni boshqarish",
        callback_data=f"admin:eps:{anime_id}"
    ))
    builder.row(InlineKeyboardButton(text="✏️ Anime tahrirlash", callback_data=f"admin:edit:{anime_id}"))
    builder.row(InlineKeyboardButton(text="🗑 Animeni o'chirish", callback_data=f"admin:delete:{anime_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Ro'yxat", callback_data="admin:list:0"))
    return builder.as_markup()


def admin_episodes_list(anime_id: int, episodes: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ep in episodes:
        num = ep["episode_number"]
        title = ep.get("title") or f"Qism {num}"
        builder.row(InlineKeyboardButton(
            text=f"📺 {num}-qism — {title}",
            callback_data=f"admin:ep:{anime_id}:{num}"
        ))
    builder.row(InlineKeyboardButton(
        text="➕ Yangi qism", callback_data=f"admin:addep:{anime_id}"
    ))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"admin:anime:{anime_id}"))
    return builder.as_markup()


def admin_episode_detail(anime_id: int, ep_num: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔄 Faylni almashtirish", callback_data=f"admin:epfile:{anime_id}:{ep_num}"
    ))
    builder.row(InlineKeyboardButton(
        text="🗑 Qismni o'chirish", callback_data=f"admin:delep:{anime_id}:{ep_num}"
    ))
    builder.row(InlineKeyboardButton(text="🔙 Qismlar", callback_data=f"admin:eps:{anime_id}"))
    return builder.as_markup()


def admin_edit_fields(anime_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    fields = [
        ("📝 Nom", "name"), ("🔑 Kod", "code"), ("📊 Status", "status"),
        ("🎬 Jami qism", "total_episodes"), ("📺 Joriy qism", "current_episode"),
        ("🌐 Tarjima", "translation"), ("🎭 Janrlar", "genres"),
        ("📢 Kanal", "channel"), ("🖼 Muqova", "thumbnail_file_id"),
        ("📄 Tavsif", "description"),
    ]
    for label, field in fields:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"admin:editfield:{anime_id}:{field}"))
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"admin:anime:{anime_id}"))
    return builder.as_markup()


def confirm_delete(anime_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"admin:confirmdelete:{anime_id}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data=f"admin:anime:{anime_id}"),
    )
    return builder.as_markup()


def confirm_delete_ep(anime_id: int, ep_num: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Ha", callback_data=f"admin:confirmdelep:{anime_id}:{ep_num}"
        ),
        InlineKeyboardButton(text="❌ Bekor", callback_data=f"admin:ep:{anime_id}:{ep_num}"),
    )
    return builder.as_markup()
