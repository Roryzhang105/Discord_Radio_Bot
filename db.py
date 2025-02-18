import sqlite3

DB_FILE = "playlist.db"

def init_db():
    """初始化数据库，创建播放列表和设置表"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS playlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT UNIQUE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # 初始化 current_index 如果不存在
    c.execute("SELECT value FROM settings WHERE key='current_index'")
    if c.fetchone() is None:
        c.execute("INSERT INTO settings (key, value) VALUES ('current_index', '0')")
    # 初始化 default_volume，如果不存在，默认 0.3
    c.execute("SELECT value FROM settings WHERE key='default_volume'")
    if c.fetchone() is None:
        c.execute("INSERT INTO settings (key, value) VALUES ('default_volume', '0.3')")
    conn.commit()
    conn.close()

def add_station(name: str, url: str) -> int:
    """将电台添加到播放列表中（如果不存在），返回该记录在列表中的索引"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO playlist (name, url) VALUES (?, ?)", (name, url))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    c.execute("SELECT id, name, url FROM playlist ORDER BY id ASC")
    playlist = c.fetchall()  # 每项为 (id, name, url)
    index = next((i for i, record in enumerate(playlist) if record[2] == url), 0)
    conn.close()
    return index

def delete_station(url: str) -> bool:
    """删除播放列表中对应 URL 的电台记录，返回是否删除成功"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM playlist WHERE url=?", (url,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def get_playlist() -> list:
    """返回播放列表，每项为字典 {'id':..., 'name':..., 'url':...}"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM playlist ORDER BY id ASC")
    playlist = [{'id': row[0], 'name': row[1], 'url': row[2]} for row in c.fetchall()]
    conn.close()
    return playlist

def get_current_index() -> int:
    """从设置表中获取当前播放电台的索引"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='current_index'")
    row = c.fetchone()
    conn.close()
    return int(row[0]) if row else 0

def set_current_index(index: int):
    """更新当前播放电台的索引到设置表中"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE settings SET value=? WHERE key='current_index'", (str(index),))
    conn.commit()
    conn.close()

def get_default_volume() -> float:
    """获取默认音量设置，默认值为 0.3"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='default_volume'")
    row = c.fetchone()
    conn.close()
    try:
        return float(row[0]) if row else 0.3
    except ValueError:
        return 0.3

def set_default_volume(volume: float):
    """更新默认音量设置到数据库中"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('default_volume', ?)", (str(volume),))
    conn.commit()
    conn.close()

# 确保在模块加载时初始化数据库
init_db()
