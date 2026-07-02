import re
from aiogram import Router, F
from aiogram.types import Message
from database.db import set_source_message_id, get_anime_by_code
from config import SOURCE_CHANNEL_ID

router = Router()

CODE_PATTERN = re.compile(r"anime\s*[ck]odi\s*[:\-]?\s*(\w+)", re.IGNORECASE)


@router.channel_post()
async def channel_post_indexer(message: Message):
    """Auto-index posts from source channel by anime code."""
    if SOURCE_CHANNEL_ID and str(message.chat.id) != str(SOURCE_CHANNEL_ID):
        return

    text = message.caption or message.text or ""
    match = CODE_PATTERN.search(text)
    if not match:
        return

    code = match.group(1).strip()
    anime = await get_anime_by_code(code)
    if anime:
        await set_source_message_id(code, message.message_id)
