import logging
import os
import json
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class Logger:
    def __init__(self, bot):
        self.bot = bot
        self.log_file = os.path.join(self.bot.base_path, 'logs', 'bot.log')
        self.activity_log_file = os.path.join(self.bot.base_path, 'logs', 'activity.log')
        self.error_log_file = os.path.join(self.bot.base_path, 'logs', 'errors.log')
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(self.bot.base_path, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Set up logging
        self.logger = logging.getLogger('AI_Discord_Bot')
        self.logger.setLevel(logging.INFO)
        
        # Create file handlers
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        activity_handler = logging.FileHandler(self.activity_log_file, encoding='utf-8')
        error_handler = logging.FileHandler(self.error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set formatters
        file_handler.setFormatter(formatter)
        activity_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(activity_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def log_activity(self, activity_type, user_id, details=None):
        """Log user activities"""
        activity_data = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': activity_type,
            'user_id': str(user_id),
            'details': details or {}
        }
        
        try:
            with open(self.activity_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(activity_data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Error logging activity: {e}")
    
    def log_model_usage(self, model_id, user_id, tokens_used, success=True, error=None):
        """Log model usage"""
        self.log_activity('model_usage', user_id, {
            'model_id': model_id,
            'tokens_used': tokens_used,
            'success': success,
            'error': error
        })
        
        # Also log to database if available
        if self.bot.db:
            try:
                cursor = self.bot.db.cursor()
                cursor.execute('''
                    INSERT INTO model_usage_logs 
                    (model_id, user_id, tokens_used, success, error_message, timestamp)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (model_id, str(user_id), tokens_used, success, error))
                self.bot.db.commit()
            except Exception as e:
                self.logger.error(f"Error logging model usage to database: {e}")
    
    def log_code_generation(self, language, user_id, success=True, error=None):
        """Log code generation"""
        self.log_activity('code_generation', user_id, {
            'language': language,
            'success': success,
            'error': error
        })
    
    def log_error(self, error_type, error_message, user_id=None, details=None):
        """Log errors"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'user_id': str(user_id) if user_id else None,
            'details': details or {}
        }
        
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')
        except Exception as e:
            # If we can't write to the error log, print to console
            print(f"CRITICAL: Could not write to error log: {e}")
        
        # Also log with the standard logger
        self.logger.error(f"{error_type}: {error_message}")
    
    def log_command_usage(self, command_name, user_id, success=True, error=None):
        """Log command usage"""
        self.log_activity('command_usage', user_id, {
            'command_name': command_name,
            'success': success,
            'error': error
        })
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
    
    def critical(self, message):
        """Log critical message"""
        self.logger.critical(message)

# Global logger instance
bot_logger = None

def get_logger(bot):
    """Get or create logger instance"""
    global bot_logger
    if bot_logger is None:
        bot_logger = Logger(bot)
    return bot_logger