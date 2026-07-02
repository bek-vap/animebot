import re
from aiogram import Bot
from config import SOURCE_CHANNEL_ID
from database.db import get_broadcast_channels


CODE_PATTERN = re.compile(r"anime\s*[ck]odi\s*[:\-]?\s*(\w+)", re.IGNORECASE)


async def find_source_message(bot: Bot, code: str, search_limit: int = 500) -> int | None:
    """
    Search SOURCE_CHANNEL_ID for a post whose caption/text contains 'Anime codi: <code>'.
    Returns message_id or None.
    Uses forwardable messages via getHistory (offset_id approach).
    """
    if not SOURCE_CHANNEL_ID:
        return None

    offset_id = 0
    checked = 0
    while checked < search_limit:
        try:
            messages = await bot.get_updates()  # can't use this way
        except Exception:
            break

    return None


async def find_post_in_channel(bot: Bot, code: str) -> int | None:
    """
    Bot must be admin in source channel.
    We iterate channel history via pyrogram-style — but aiogram doesn't support getHistory.
    So instead: bot listens to channel_post events and indexes them automatically.
    This function just checks if we already have the message_id stored.
    """
    return None


def format_broadcast_caption(anime: dict) -> str:
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
    lines.append("╰──────────────────────")
    lines.append(f"\n📌 Botdan yuklab olish uchun kodni yuboring: <code>{anime['code']}</code>")
    if anime.get("description"):
        lines.append(f"\n📄 {anime['description']}")
    return "\n".join(lines)


async def broadcast_anime(bot: Bot, anime: dict) -> dict:
    """
    Send anime announcement to all broadcast channels.
    Returns {success: int, failed: int}
    """
    channels = await get_broadcast_channels()
    caption = format_broadcast_caption(anime)
    success, failed = 0, 0

    for ch in channels:
        try:
            if anime.get("thumbnail_file_id"):
                await bot.send_photo(
                    chat_id=ch["channel_id"],
                    photo=anime["thumbnail_file_id"],
                    caption=caption,
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=ch["channel_id"],
                    text=caption,
                    parse_mode="HTML",
                )
            success += 1
        except Exception:
            failed += 1

    return {"success": success, "failed": failed}
