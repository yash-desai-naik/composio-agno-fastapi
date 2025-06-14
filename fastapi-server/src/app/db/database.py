import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path: str = "composio.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            connected_apps TEXT NOT NULL,
            chat_history TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    def create_user(self, email: str, name: str, entity_id: str) -> dict:
        conn = self.get_connection()
        cursor = conn.cursor()

        user_data = {
            "email": email,
            "name": name,
            "entity_id": entity_id,
            "connected_apps": json.dumps([]),
            "chat_history": json.dumps([]),
            "created_at": datetime.now().isoformat()
        }

        cursor.execute("""
        INSERT INTO users (email, name, entity_id, connected_apps, chat_history, created_at)
        VALUES (:email, :name, :entity_id, :connected_apps, :chat_history, :created_at)
        """, user_data)

        conn.commit()
        conn.close()
        return self.get_user(email)

    def get_user(self, email: str) -> Optional[dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_dict = dict(user)
            user_dict['connected_apps'] = json.loads(user_dict['connected_apps'])
            user_dict['chat_history'] = json.loads(user_dict['chat_history'])
            return user_dict
        return None

    def update_user_apps(self, email: str, connected_apps: List[str]):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users SET connected_apps = ?
        WHERE email = ?
        """, (json.dumps(connected_apps), email))

        conn.commit()
        conn.close()

    def update_chat_history(self, email: str, chat_history: List[Dict]):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users SET chat_history = ?
        WHERE email = ?
        """, (json.dumps(chat_history), email))

        conn.commit()
        conn.close()

db = Database()
