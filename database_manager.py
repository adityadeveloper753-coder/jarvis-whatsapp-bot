import sqlite3
from datetime import datetime
import time

class JARVISDatabase:
    def __init__(self, db_name="jarvis_core.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_tables()
        self.set_default_favorites()

    def setup_tables(self):
        """Creates tables for tasks, preferences, chat memory, and WhatsApp blocklist."""
        # 1. Task Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                task_name TEXT,
                category TEXT,
                is_completed BOOLEAN DEFAULT 0,
                start_time REAL,
                completion_time REAL
            )
        ''')
        
        # 2. User Profile Table (Favorites)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                preference_key TEXT UNIQUE,
                preference_value TEXT
            )
        ''')

        # 3. Chat History Table (Local Free Memory)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                sender TEXT,
                message TEXT
            )
        ''')

        # 4. 🔥 NEW: WhatsApp Blocklist Table (Inko reply nahi jayega)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS whatsapp_blocklist (
                phone_number TEXT UNIQUE
            )
        ''')
        self.conn.commit()

    # --- 🔥 NEW: WHATSAPP BLOCKLIST FUNCTIONS ---
    def block_number_from_bot(self, phone_number):
        """Is number ko bot reply nahi karega (Family/Friends bypass)"""
        # Phone number format simple string hona chahiye, jaise: "+919876543210" ya "Adi"
        self.cursor.execute("INSERT OR REPLACE INTO whatsapp_blocklist (phone_number) VALUES (?)", (phone_number,))
        self.conn.commit()
        return f"Number {phone_number} successfully added to WhatsApp bypass list."

    def unblock_number_from_bot(self, phone_number):
        """Number ko blocklist se hatane ke liye"""
        self.cursor.execute("DELETE FROM whatsapp_blocklist WHERE phone_number=?", (phone_number,))
        self.conn.commit()
        return f"Number {phone_number} removed from bypass list."

    def is_number_blocked(self, phone_number):
        """Check karega ki kya yeh number list mein hai"""
        self.cursor.execute("SELECT * FROM whatsapp_blocklist WHERE phone_number=?", (phone_number,))
        return self.cursor.fetchone() is not None

    # --- CHAT MEMORY FUNCTIONS ---
    def save_chat(self, sender, message):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('INSERT INTO chat_history (timestamp, sender, message) VALUES (?, ?, ?)', (now, sender, message))
        self.conn.commit()

    def get_recent_context(self, limit=6):
        self.cursor.execute('SELECT sender, message FROM chat_history ORDER BY id DESC LIMIT ?', (limit,))
        rows = self.cursor.fetchall()
        rows.reverse()
        context_str = ""
        for row in rows:
            context_str += f"[{row[0]}]: {row[1]}\n"
        return context_str

    # --- PREFERENCES FUNCTIONS ---
    def set_preference(self, key, value):
        self.cursor.execute('INSERT OR REPLACE INTO user_profile (preference_key, preference_value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    def get_preference(self, key):
        self.cursor.execute("SELECT preference_value FROM user_profile WHERE preference_key=?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def set_default_favorites(self):
        if not self.get_preference("favorite_song"):
            self.set_preference("favorite_song", "Not Set")
            self.set_preference("language", "Hindi/English")
            self.set_preference("country", "India")
            self.set_preference("favorite_subject", "Cybersecurity")
            self.set_preference("location", "India")

    # --- TASKS FUNCTIONS ---
    def get_today_date(self):
        return datetime.now().strftime("%Y-%m-%d")

    def add_task(self, task_name, category="General"):
        today = self.get_today_date()
        self.cursor.execute("SELECT * FROM daily_tasks WHERE date=? AND task_name=?", (today, task_name))
        if self.cursor.fetchone():
            return False, "Task already exists."
        self.cursor.execute('INSERT INTO daily_tasks (date, task_name, category, start_time) VALUES (?, ?, ?, ?)', (today, task_name, category, time.time()))
        self.conn.commit()
        return True, f"Task '{task_name}' added."

    def get_pending_tasks(self):
        self.cursor.execute("SELECT task_name FROM daily_tasks WHERE date=? AND is_completed=0", (self.get_today_date(),))
        return [row[0] for row in self.cursor.fetchall()]

    def mark_task_complete(self, task_name):
        self.cursor.execute('UPDATE daily_tasks SET is_completed=1, completion_time=? WHERE date=? AND task_name LIKE ? AND is_completed=0', (time.time(), self.get_today_date(), f"%{task_name}%"))
        self.conn.commit()
        return self.cursor.rowcount > 0