# utils/helpers.py - وظائف مساعدة
import discord
import json
import os
from datetime import datetime, timedelta
import aiohttp
import asyncio

async def load_json(file_path):
    """تحميل ملف JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"خطأ في تحميل الملف {file_path}: {e}")
        return {}

async def save_json(file_path, data):
    """حفظ بيانات إلى ملف JSON"""
    try:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"خطأ في حفظ الملف {file_path}: {e}")
        return False

def chunk_message(message, max_length=2000):
    """تقسيم الرسائل الطويلة"""
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    while len(message) > 0:
        # البحث عن نقطة نهاية مناسبة
        if len(message) <= max_length:
            chunks.append(message)
            break
        
        # محاولة التقسيم عند نهاية الجملة
        split_point = message[:max_length].rfind('\n')
        if split_point == -1:
            # إذا لم يتم العثور على سطر جديد، قسم عند المسافة
            split_point = message[:max_length].rfind(' ')
        
        if split_point == -1:
            # إذا لم يتم العثور على مسافة، قسم عند الحد الأقصى
            split_point = max_length
        
        chunks.append(message[:split_point])
        message = message[split_point:].strip()
    
    return chunks

async def get_user_stats(bot, user_id):
    """الحصول على إحصائيات المستخدم"""
    cursor = bot.db.cursor()
    cursor.execute(
        "SELECT messages_sent, commands_used, tokens_used, preferred_model, last_active FROM user_stats WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        return {
            "messages_sent": 0,
            "commands_used": 0,
            "tokens_used": 0,
            "preferred_model": "default",
            "last_active": "لم يستخدم البوت بعد"
        }
    
    return {
        "messages_sent": result[0],
        "commands_used": result[1],
        "tokens_used": result[2],
        "preferred_model": result[3],
        "last_active": result[4]
    }

async def get_system_stats(bot):
    """الحصول على إحصائيات النظام"""
    cursor = bot.db.cursor()
    
    # إجمالي المستخدمين
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_stats")
    total_users = cursor.fetchone()[0]
    
    # المستخدمين النشطين اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_stats WHERE last_active LIKE ?", (f"{today}%",))
    active_users_today = cursor.fetchone()[0]
    
    # إجمالي الرسائل
    cursor.execute("SELECT SUM(messages_sent) FROM user_stats")
    total_messages = cursor.fetchone()[0] or 0
    
    # إجمالي الأوامر
    cursor.execute("SELECT SUM(commands_used) FROM user_stats")
    total_commands = cursor.fetchone()[0] or 0
    
    # إجمالي التوكنز
    cursor.execute("SELECT SUM(tokens_used) FROM user_stats")
    total_tokens = cursor.fetchone()[0] or 0
    
    # النماذج المستخدمة
    cursor.execute("SELECT model_name, usage_count FROM system_stats WHERE stat_type = 'model_usage'")
    models_usage = cursor.fetchall()
    
    return {
        "total_users": total_users,
        "active_users_today": active_users_today,
        "total_messages": total_messages,
        "total_commands": total_commands,
        "total_tokens": total_tokens,
        "models_usage": dict(models_usage) if models_usage else {}
    }

def format_time_difference(timestamp_str):
    """تنسيق الفرق الزمني بشكل مقروء"""
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
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

async def fetch_openrouter_models(api_key):
    """جلب قائمة النماذج المتاحة من OpenRouter"""
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    print(f"خطأ في جلب النماذج: {response.status}")
                    return []
    except Exception as e:
        print(f"خطأ في الاتصال بـ OpenRouter: {e}")
        return []