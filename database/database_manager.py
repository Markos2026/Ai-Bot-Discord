# database/database_manager.py - مدير قاعدة البيانات
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time

class DatabaseManager:
    def __init__(self, db_path='database/models.sqlite'):
        self.db_path = db_path
        self.connection = None
        self.cache = {}  # In-memory cache
        self.cache_lock = threading.Lock()  # Thread lock for cache access
        self.cache_timeout = 300  # 5 minutes cache timeout
        self.cache_cleanup_interval = 3600  # 1 hour cleanup interval
        self.connect()
        self.create_tables()
        self.start_cache_cleanup()
    
    def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            return False
    
    def start_cache_cleanup(self):
        """Start periodic cache cleanup"""
        def cleanup():
            while True:
                time.sleep(self.cache_cleanup_interval)
                with self.cache_lock:
                    current_time = datetime.now()
                    expired_keys = [
                        key for key, (_, timestamp) in self.cache.items()
                        if (current_time - timestamp).total_seconds() > self.cache_timeout
                    ]
                    for key in expired_keys:
                        del self.cache[key]
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def get_cached(self, key):
        """Get data from cache if available and not expired"""
        with self.cache_lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if (datetime.now() - timestamp).total_seconds() < self.cache_timeout:
                    return data
                else:
                    # Remove expired cache entry
                    del self.cache[key]
        return None
    
    def set_cache(self, key, data):
        """Set data in cache"""
        with self.cache_lock:
            self.cache[key] = (data, datetime.now())
    
    def create_tables(self):
        """إنشاء الجداول اللازمة"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # جدول النماذج المخصصة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    display_name TEXT NOT NULL,
                    model_id TEXT NOT NULL UNIQUE,
                    api_key TEXT NOT NULL,
                    added_by TEXT NOT NULL,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    usage_count INTEGER DEFAULT 0,
                    performance_rating FLOAT DEFAULT 0.0,
                    last_used DATETIME
                )
            ''')
            
            # جدول إحصائيات المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    total_messages INTEGER DEFAULT 0,
                    commands_used INTEGER DEFAULT 0,
                    preferred_model TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    last_active DATETIME,
                    message_limit INTEGER DEFAULT 1000,
                    is_premium BOOLEAN DEFAULT FALSE,
                    joined_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول سجلات المحادثات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    message_content TEXT,
                    response_content TEXT,
                    model_used TEXT,
                    tokens_used INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول سجلات توليد الكود
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_generation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    request_content TEXT,
                    response_content TEXT,
                    language TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول سجلات استخدام النماذج
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    tokens_used INTEGER,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول إحصائيات النظام
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_stats (
                    stat_date DATE PRIMARY KEY,
                    total_messages INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    successful_responses INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    uptime_seconds INTEGER DEFAULT 0
                )
            ''')
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"خطأ في إنشاء الجداول: {e}")
            return False
    
    def get_user_stats(self, user_id):
        """الحصول على إحصائيات المستخدم"""
        # Check cache first
        cache_key = f"user_stats_{user_id}"
        cached = self.get_cached(cache_key)
        if cached is not None:
            return cached
        
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (str(user_id),))
            result = cursor.fetchone()
            
            # Cache the result
            self.set_cache(cache_key, result)
            return result
        except Exception as e:
            print(f"خطأ في الحصول على إحصائيات المستخدم: {e}")
            return None
    
    def update_user_stats(self, user_id, username, commands_used=0, tokens_used=0, preferred_model=None):
        """تحديث إحصائيات المستخدم"""
        # Invalidate cache
        cache_key = f"user_stats_{user_id}"
        with self.cache_lock:
            if cache_key in self.cache:
                del self.cache[cache_key]
        
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_stats 
                (user_id, username, commands_used, tokens_used, preferred_model, last_active) 
                VALUES (?, ?, 
                    COALESCE((SELECT commands_used FROM user_stats WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT tokens_used FROM user_stats WHERE user_id = ?), 0) + ?,
                    COALESCE(?, (SELECT preferred_model FROM user_stats WHERE user_id = ?)),
                    CURRENT_TIMESTAMP)
            ''', (str(user_id), str(username), str(user_id), commands_used, str(user_id), tokens_used, preferred_model, str(user_id)))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"خطأ في تحديث إحصائيات المستخدم: {e}")
            return False
    
    def log_conversation(self, user_id, channel_id, message_content, response_content, model_used, tokens_used):
        """تسجيل محادثة"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO conversation_logs 
                (user_id, channel_id, message_content, response_content, model_used, tokens_used)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(user_id), str(channel_id), message_content, response_content, model_used, tokens_used))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"خطأ في تسجيل المحادثة: {e}")
            return False
    
    def log_model_usage(self, model_id, user_id, tokens_used, success=True, error_message=None):
        """Log model usage"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO model_usage_logs 
                (model_id, user_id, tokens_used, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (model_id, str(user_id), tokens_used, success, error_message))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error logging model usage: {e}")
            return False
    
    def get_custom_models(self):
        """الحصول على جميع النماذج المخصصة"""
        # Check cache first
        cached = self.get_cached("custom_models")
        if cached is not None:
            return cached
        
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM custom_models WHERE is_active = ?", (True,))
            result = cursor.fetchall()
            
            # Cache the result
            self.set_cache("custom_models", result)
            return result
        except Exception as e:
            print(f"خطأ في الحصول على النماذج المخصصة: {e}")
            return []
    
    def add_custom_model(self, display_name, model_id, api_key, added_by):
        """إضافة نموذج مخصص"""
        # Invalidate cache
        with self.cache_lock:
            if "custom_models" in self.cache:
                del self.cache["custom_models"]
        
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO custom_models (display_name, model_id, api_key, added_by)
                VALUES (?, ?, ?, ?)
            ''', (display_name, model_id, api_key, str(added_by)))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"خطأ في إضافة النموذج المخصص: {e}")
            return None
    
    def remove_custom_model(self, model_id):
        """إزالة نموذج مخصص"""
        # Invalidate cache
        with self.cache_lock:
            if "custom_models" in self.cache:
                del self.cache["custom_models"]
        
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM custom_models WHERE model_id = ?", (model_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"خطأ في إزالة النموذج المخصص: {e}")
            return False
    
    def update_system_stats(self, stat_date, total_messages=0, active_users=0, successful_responses=0, total_errors=0, uptime_seconds=0):
        """تحديث إحصائيات النظام"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_stats 
                (stat_date, total_messages, active_users, successful_responses, total_errors, uptime_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (stat_date, total_messages, active_users, successful_responses, total_errors, uptime_seconds))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"خطأ في تحديث إحصائيات النظام: {e}")
            return False
    
    def log_code_generation(self, user_id, request_content, response_content, language, success=True, error_message=None):
        """تسجيل توليد الكود"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO code_generation_logs 
                (user_id, request_content, response_content, language, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(user_id), request_content, response_content, language, success, error_message))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"خطأ في تسجيل توليد الكود: {e}")
            return False
    
    def get_code_generation_stats(self, user_id=None, days=30):
        """الحصول على إحصائيات توليد الكود"""
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            if user_id:
                cursor.execute('''
                    SELECT language, COUNT(*) as count, AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate
                    FROM code_generation_logs 
                    WHERE user_id = ? AND timestamp > datetime('now', '-{} days')
                    GROUP BY language
                '''.format(days), (str(user_id),))
            else:
                cursor.execute('''
                    SELECT language, COUNT(*) as count, AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate
                    FROM code_generation_logs 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY language
                '''.format(days))
            return cursor.fetchall()
        except Exception as e:
            print(f"خطأ في الحصول على إحصائيات توليد الكود: {e}")
            return None
    
    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()

# استخدام المدير كنموذج فردي
db_manager = None

def get_db_manager():
    """الحصول على نسخة من مدير قاعدة البيانات"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager