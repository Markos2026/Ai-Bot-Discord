# utils/formatters.py - أدوات التنسيق
import re
from datetime import datetime, timedelta

def format_time_difference(timestamp_str):
    """تنسيق الفرق الزمني بشكل مقروء"""
    try:
        if isinstance(timestamp_str, str):
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        else:
            timestamp = timestamp_str
            
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} يوم"
        elif diff.seconds // 3600 > 0:
            return f"{diff.seconds // 3600} ساعة"
        elif diff.seconds // 60 > 0:
            return f"{diff.seconds // 60} دقيقة"
        else:
            return f"{diff.seconds} ثانية"
    except:
        return "غير معروف"

def format_large_number(num):
    """تنسيق الأرقام الكبيرة"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def truncate_text(text, max_length=100):
    """اقتطاع النص إذا تجاوز الطول المحدد"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_model_name(model_id):
    """تنسيق اسم النموذج"""
    # إزالة البائع من اسم النموذج إذا كان موجوداً
    if "/" in model_id:
        return model_id.split("/")[-1]
    return model_id

def sanitize_input(text):
    """تنقية المدخلات من الأحرف الخاصة الخطرة"""
    # إزالة الأحرف غير الآمنة
    sanitized = re.sub(r'[<>@!`]', '', text)
    return sanitized.strip()

def format_bytes(bytes_count):
    """تنسيق حجم البيانات بالبايت"""
    if bytes_count >= 1024*1024*1024:
        return f"{bytes_count/(1024*1024*1024):.2f} GB"
    elif bytes_count >= 1024*1024:
        return f"{bytes_count/(1024*1024):.2f} MB"
    elif bytes_count >= 1024:
        return f"{bytes_count/1024:.2f} KB"
    else:
        return f"{bytes_count} B"

def format_duration(seconds):
    """تنسيق المدة الزمنية"""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    elif seconds >= 60:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        return f"{seconds}s"

def escape_markdown(text):
    """تحويل الأحرف الخاصة في ماركداون"""
    # تجنب الأحرف الخاصة في ماركداون
    escape_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text