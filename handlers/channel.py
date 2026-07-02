import re
import logging
from aiogram import Router, F
from aiogram.types import Message
from database.db import set_source_message_id, get_anime_by_code
from config import SOURCE_CHANNEL_ID

router = Router()
log = logging.getLogger(__name__)

CODE_PATTERN = re.compile(r"anime\s*[ck]odi\s*[:\-]?\s*(\w+)", re.IGNORECASE)


@router.channel_post()
async def channel_post_indexer(message: Message):
    """Auto-index posts from source channel by anime code."""
    log.info(f"[CHANNEL] post received: chat_id={message.chat.id} msg_id={message.message_id}")

    if SOURCE_CHANNEL_ID and str(message.chat.id) != str(SOURCE_CHANNEL_ID):
        log.info(f"[CHANNEL] skip: not source channel ({message.chat.id} != {SOURCE_CHANNEL_ID})")
        return

    text = message.caption or message.text or ""
    match = CODE_PATTERN.search(text)
    if not match:
        log.info(f"[CHANNEL] no code found in: {text[:80]!r}")
        return

    code = match.group(1).strip()
    log.info(f"[CHANNEL] found code={code!r}")

    anime = await get_anime_by_code(code)
    if anime:
        await set_source_message_id(code, message.message_id)
        log.info(f"[CHANNEL] indexed: code={code} message_id={message.message_id} anime={anime['name']}")
    else:
        log.warning(f"[CHANNEL] code={code!r} not found in DB")
