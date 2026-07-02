import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Majburiy obuna kanallari
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sub_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_link TEXT NOT NULL
            )
        """)
        # Anime post yuboriladigan kanallar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS broadcast_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_name TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'Tugallangan',
                total_episodes INTEGER DEFAULT 0,
                current_episode INTEGER DEFAULT 0,
                translation TEXT DEFAULT '',
                genres TEXT DEFAULT '',
                thumbnail_file_id TEXT DEFAULT '',
                description TEXT DEFAULT '',
                source_message_id INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, anime_id)
            )
        """)
        await db.commit()


# ─── ANIME ───────────────────────────────────────────────────────────────────

async def get_anime_by_code(code: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM animes WHERE code = ?", (code.strip(),)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_anime_by_id(anime_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM animes WHERE id = ?", (anime_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_anime(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO animes
            (code, name, status, total_episodes, current_episode, translation, genres, thumbnail_file_id, description, source_message_id)
            VALUES
            (:code, :name, :status, :total_episodes, :current_episode, :translation, :genres, :thumbnail_file_id, :description, :source_message_id)
        """, data)
        await db.commit()
        return cursor.lastrowid


async def update_anime(anime_id: int, data: dict):
    fields = ", ".join(f"{k} = :{k}" for k in data)
    data["id"] = anime_id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE animes SET {fields} WHERE id = :id", data)
        await db.commit()


async def set_source_message_id(code: str, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE animes SET source_message_id = ? WHERE code = ?", (message_id, code))
        await db.commit()


async def delete_anime(anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM animes WHERE id = ?", (anime_id,))
        await db.commit()


async def list_animes(offset: int = 0, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM animes ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
        ) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def count_animes() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM animes") as cursor:
            return (await cursor.fetchone())[0]


# ─── USERS ───────────────────────────────────────────────────────────────────

async def register_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def count_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            return (await cursor.fetchone())[0]


async def add_history(user_id: int, anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO user_history (user_id, anime_id) VALUES (?, ?)", (user_id, anime_id))
        await db.commit()


async def get_user_history(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT a.name, a.code, h.watched_at
            FROM user_history h JOIN animes a ON h.anime_id = a.id
            WHERE h.user_id = ? ORDER BY h.watched_at DESC LIMIT 10
        """, (user_id,)) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def add_favorite(user_id: int, anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO favorites (user_id, anime_id) VALUES (?, ?)", (user_id, anime_id))
        await db.commit()


async def remove_favorite(user_id: int, anime_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM favorites WHERE user_id = ? AND anime_id = ?", (user_id, anime_id))
        await db.commit()


async def get_favorites(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT a.name, a.code FROM favorites f
            JOIN animes a ON f.anime_id = a.id
            WHERE f.user_id = ? ORDER BY f.added_at DESC
        """, (user_id,)) as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def is_favorite(user_id: int, anime_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM favorites WHERE user_id=? AND anime_id=?", (user_id, anime_id)) as c:
            return await c.fetchone() is not None


# ─── ADMINS ──────────────────────────────────────────────────────────────────

async def is_admin_in_db(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)) as c:
            return await c.fetchone() is not None


async def add_admin(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id, username, full_name) VALUES (?,?,?)",
                         (user_id, username, full_name))
        await db.commit()


async def list_admins() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins ORDER BY added_at") as c:
            return [dict(r) for r in await c.fetchall()]


# ─── SUBSCRIPTION CHANNELS ───────────────────────────────────────────────────

async def get_sub_channels() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sub_channels") as c:
            return [dict(r) for r in await c.fetchall()]


async def add_sub_channel(channel_id: str, channel_name: str, channel_link: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO sub_channels (channel_id, channel_name, channel_link) VALUES (?,?,?)",
                         (channel_id, channel_name, channel_link))
        await db.commit()


async def delete_sub_channel(row_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sub_channels WHERE id = ?", (row_id,))
        await db.commit()


# ─── BROADCAST CHANNELS ──────────────────────────────────────────────────────

async def get_broadcast_channels() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM broadcast_channels") as c:
            return [dict(r) for r in await c.fetchall()]


async def add_broadcast_channel(channel_id: str, channel_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO broadcast_channels (channel_id, channel_name) VALUES (?,?)",
                         (channel_id, channel_name))
        await db.commit()


async def delete_broadcast_channel(row_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM broadcast_channels WHERE id = ?", (row_id,))
        await db.commit()
