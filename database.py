import sqlite3
from datetime import datetime
import pytz

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('jitsuna.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            timezone TEXT DEFAULT 'UTC',
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            reminder_hour INTEGER DEFAULT None
        )
        ''')
        
        # Habits table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            streak INTEGER DEFAULT 0,
            last_completed_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id: int, username: str):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                      (user_id, username))
        self.conn.commit()
    
    def get_user_habits(self, user_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute('SELECT habit_id, name, streak, last_completed_date FROM habits WHERE user_id = ?',
                      (user_id,))
        return cursor.fetchall()
    
    def add_habit(self, user_id: int, name: str) -> bool:
        cursor = self.conn.cursor()
        # Check habit limit
        cursor.execute('SELECT COUNT(*) FROM habits WHERE user_id = ?', (user_id,))
        if cursor.fetchone()[0] >= 8:
            return False
        
        cursor.execute('''
        INSERT INTO habits (user_id, name) VALUES (?, ?)
        ''', (user_id, name))
        self.conn.commit()
        return True
    
    def remove_habit(self, user_id: int, name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM habits WHERE user_id = ? AND name = ?',
                      (user_id, name))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def toggle_habit(self, user_id: int, habit_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT last_completed_date FROM habits 
        WHERE habit_id = ? AND user_id = ?
        ''', (habit_id, user_id))
        result = cursor.fetchone()
        
        if not result:
            return False
            
        last_completed = result[0]
        today = datetime.now().strftime('%Y-%m-%d')
        
        if last_completed == today:
            # Uncomplete
            cursor.execute('''
            UPDATE habits SET last_completed_date = NULL 
            WHERE habit_id = ? AND user_id = ?
            ''', (habit_id, user_id))
        else:
            # Complete
            cursor.execute('''
            UPDATE habits SET last_completed_date = ? 
            WHERE habit_id = ? AND user_id = ?
            ''', (today, habit_id, user_id))
            
        self.conn.commit()
        return True
    
    def get_user_xp(self, user_id: int) -> tuple:
        cursor = self.conn.cursor()
        cursor.execute('SELECT xp, level FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def add_xp(self, user_id: int, amount: int):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET xp = xp + ?,
            level = (xp + ?) / 50 + 1
        WHERE user_id = ?
        ''', (amount, amount, user_id))
        self.conn.commit()
    
    def set_reminder(self, user_id: int, hour: int):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users SET reminder_hour = ? WHERE user_id = ?
        ''', (hour, user_id))
        self.conn.commit()
    
    def get_reminder(self, user_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT reminder_hour FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None 