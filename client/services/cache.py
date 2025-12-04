"""
本地缓存 - SQLite 存储
"""
import sqlite3
import json
import time
from pathlib import Path
from typing import Any, Optional, List, Dict
from contextlib import contextmanager


class CacheManager:
    """缓存管理器 - 使用 SQLite 存储"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with self._get_conn() as conn:
            conn.executescript('''
                -- 通用键值缓存
                CREATE TABLE IF NOT EXISTS kv_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- 好友列表缓存
                CREATE TABLE IF NOT EXISTS friends (
                    user_id TEXT PRIMARY KEY,
                    nickname TEXT,
                    avatar TEXT,
                    status TEXT DEFAULT 'offline',
                    last_online REAL,
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- 最近房间
                CREATE TABLE IF NOT EXISTS recent_rooms (
                    room_id TEXT PRIMARY KEY,
                    game_type TEXT,
                    name TEXT,
                    host_name TEXT,
                    joined_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- 聊天记录
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT,
                    sender_id TEXT,
                    sender_name TEXT,
                    content TEXT,
                    timestamp REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- 游戏回放
                CREATE TABLE IF NOT EXISTS game_replays (
                    replay_id TEXT PRIMARY KEY,
                    game_type TEXT,
                    players TEXT,  -- JSON
                    data BLOB,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- 索引
                CREATE INDEX IF NOT EXISTS idx_chat_channel ON chat_messages(channel);
                CREATE INDEX IF NOT EXISTS idx_chat_time ON chat_messages(timestamp);
            ''')
    
    @contextmanager
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    # ========== 键值缓存 ==========
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        expires_at = time.time() + ttl if ttl else None
        value_json = json.dumps(value, ensure_ascii=False)
        
        with self._get_conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO kv_cache (key, value, expires_at)
                VALUES (?, ?, ?)
            ''', (key, value_json, expires_at))
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT value, expires_at FROM kv_cache WHERE key = ?',
                (key,)
            ).fetchone()
            
            if row:
                # 检查过期
                if row['expires_at'] and row['expires_at'] < time.time():
                    conn.execute('DELETE FROM kv_cache WHERE key = ?', (key,))
                    return default
                return json.loads(row['value'])
        return default
    
    def delete(self, key: str):
        """删除缓存"""
        with self._get_conn() as conn:
            conn.execute('DELETE FROM kv_cache WHERE key = ?', (key,))
    
    # ========== 好友缓存 ==========
    
    def cache_friends(self, friends: List[Dict]):
        """缓存好友列表"""
        with self._get_conn() as conn:
            for f in friends:
                conn.execute('''
                    INSERT OR REPLACE INTO friends 
                    (user_id, nickname, avatar, status, last_online, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    f.get('user_id'),
                    f.get('nickname'),
                    f.get('avatar'),
                    f.get('status', 'offline'),
                    f.get('last_online'),
                    time.time()
                ))
    
    def get_friends(self) -> List[Dict]:
        """获取缓存的好友列表"""
        with self._get_conn() as conn:
            rows = conn.execute('SELECT * FROM friends ORDER BY status DESC, nickname').fetchall()
            return [dict(row) for row in rows]
    
    # ========== 最近房间 ==========
    
    def add_recent_room(self, room: Dict):
        """添加最近房间"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO recent_rooms
                (room_id, game_type, name, host_name, joined_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                room.get('room_id'),
                room.get('game_type'),
                room.get('name'),
                room.get('host_name'),
                time.time()
            ))
            
            # 只保留最近 20 条
            conn.execute('''
                DELETE FROM recent_rooms WHERE room_id NOT IN (
                    SELECT room_id FROM recent_rooms ORDER BY joined_at DESC LIMIT 20
                )
            ''')
    
    def get_recent_rooms(self, limit: int = 10) -> List[Dict]:
        """获取最近房间"""
        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM recent_rooms ORDER BY joined_at DESC LIMIT ?',
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # ========== 聊天记录 ==========
    
    def save_message(self, channel: str, sender_id: str, sender_name: str, content: str):
        """保存聊天消息"""
        with self._get_conn() as conn:
            conn.execute('''
                INSERT INTO chat_messages (channel, sender_id, sender_name, content)
                VALUES (?, ?, ?, ?)
            ''', (channel, sender_id, sender_name, content))
            
            # 只保留每个频道最近 500 条
            conn.execute('''
                DELETE FROM chat_messages WHERE channel = ? AND id NOT IN (
                    SELECT id FROM chat_messages WHERE channel = ? 
                    ORDER BY timestamp DESC LIMIT 500
                )
            ''', (channel, channel))
    
    def get_messages(self, channel: str, limit: int = 50) -> List[Dict]:
        """获取聊天记录"""
        with self._get_conn() as conn:
            rows = conn.execute('''
                SELECT * FROM chat_messages WHERE channel = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (channel, limit)).fetchall()
            return [dict(row) for row in reversed(rows)]
    
    # ========== 清理 ==========
    
    def cleanup(self):
        """清理过期数据"""
        now = time.time()
        with self._get_conn() as conn:
            # 清理过期的键值缓存
            conn.execute('DELETE FROM kv_cache WHERE expires_at < ?', (now,))
            
            # 清理 30 天前的聊天记录
            threshold = now - 30 * 24 * 3600
            conn.execute('DELETE FROM chat_messages WHERE timestamp < ?', (threshold,))

