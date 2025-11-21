# cogs/ai_chat.py - نظام الدردشة الذكي
import discord
from discord.ext import commands
import aiohttp
import json
import asyncio
from datetime import datetime
import re

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
    
    async def generate_response(self, message, user_id, model_id=None):
        """توليد رد من الذكاء الاصطناعي باستخدام OpenRouter"""
        try:
            # تحديد النموذج المستخدم
            if not model_id:
                model_id = self.bot.config.get("settings", {}).get("default_model", "tngtech/deepseek-r1t2-chimera:free")
            
            # الحصول على مفتاح API للنموذج
            model_config = self.bot.available_models.get(model_id, {})
            api_key = model_config.get("api_key")
            
            # إذا لم يكن هناك مفتاح API مخصص، استخدم المفتاح الافتراضي
            if not api_key:
                # في الإصدار النهائي، يجب الحصول على مفتاح API من متغيرات البيئة
                api_key = "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"
            
            # تحضير بيانات الطلب
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # إرسال الطلب إلى OpenRouter API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://discord.com",  # اختياري
                "X-Title": "AI Discord Bot"  # اختياري
            }
            
            async with self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ai_response = data["choices"][0]["message"]["content"]
                    
                    # تصفية الرد لإزالة التفكير وعرض الرد النهائي فقط
                    filtered_response = self.filter_ai_response(ai_response)
                    
                    # تنسيق الرد إذا كان يحتوي على كود
                    formatted_response = self.format_code_response(filtered_response)
                    
                    # التأكد من أن الرد ليس فارغًا
                    if not formatted_response or formatted_response.strip() == "":
                        formatted_response = "I'm sorry, I couldn't generate a proper response. Please try rephrasing your question."
                    
                    # تحديث إحصائيات المستخدم
                    await self.update_user_stats(user_id, model_id, len(message) + len(formatted_response))
                    
                    # تسجيل المحادثة
                    await self.log_conversation(user_id, message, formatted_response, model_id)
                    
                    # تسجيل استخدام النموذج
                    await self.log_model_usage(model_id, user_id, len(message) + len(formatted_response), True)
                    
                    return formatted_response
                else:
                    error_text = await response.text()
                    error_msg = f"Error in OpenRouter API: {response.status} - {error_text}"
                    print(error_msg)
                    
                    # Log error
                    await self.log_model_usage(model_id, user_id, 0, False, error_msg)
                    
                    return "Sorry, an error occurred while connecting to the AI service. Please try again later."
        
        except Exception as e:
            error_msg = f"Error generating response: {e}"
            print(error_msg)
            
            # Log error
            await self.log_model_usage(model_id, user_id, 0, False, error_msg)
            
            return "Sorry, an unexpected error occurred. Please try again later."

    async def log_model_usage(self, model_id, user_id, tokens_used, success=True, error=None):
        """Log model usage"""
        if not self.bot.db:
            return
        try:
            cursor = self.bot.db.cursor()
            cursor.execute('''
                INSERT INTO model_usage_logs 
                (model_id, user_id, tokens_used, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                model_id,
                str(user_id),
                tokens_used,
                success,
                error
            ))
            self.bot.db.commit()
        except Exception as e:
            print(f"Error logging model usage: {e}")

    def is_programming_request(self, message):
        """Detect if the message is a programming request"""
        programming_keywords = [
            'code', 'program', 'script', 'function', 'class', 'method', 'algorithm',
            'python', 'javascript', 'java', 'c++', 'c#', 'html', 'css', 'sql',
            'write a', 'create a', 'make a', 'develop a', 'build a',
            'how to', 'can you', 'please', 'help me', 'need help',
            'debug', 'fix', 'error', 'bug', 'issue', 'generate'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in programming_keywords)

    def extract_code_from_response(self, response):
        """Extract code from AI response"""
        # Look for code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            return code_blocks
        
        # If no code blocks found, check if response looks like code
        lines = response.split('\n')
        code_line_count = 0
        code_patterns = [
            r'^\s*def\s+\w+\s*\(',  # Python function definition
            r'^\s*class\s+\w+',     # Class definition
            r'^\s*import\s+\w+',    # Import statement
            r'^\s*from\s+\w+',      # From import statement
            r'^\s*function\s+\w+',  # JavaScript function
            r'^\s*const\s+\w+',     # JavaScript const
            r'^\s*let\s+\w+',       # JavaScript let
            r'^\s*var\s+\w+',       # JavaScript var
            r'^\s*public\s+class',  # Java class
            r'^\s*public\s+static', # Java static method
            r'^\s*package\s+\w+',   # Java package
            r'^\s*#include\s*<',    # C/C++ include
            r'^\s*using\s+namespace'
        ]
        
        for line in lines:
            for pattern in code_patterns:
                if re.match(pattern, line):
                    code_line_count += 1
                    break
        
        # If more than 30% of lines look like code, treat entire response as code
        if len(lines) > 0 and code_line_count / len(lines) > 0.3:
            # Try to detect language based on patterns
            python_count = sum(1 for line in lines if re.match(r'^\s*(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+)', line))
            js_count = sum(1 for line in lines if re.match(r'^\s*(function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+)', line))
            java_count = sum(1 for line in lines if re.match(r'^\s*(public\s+|package\s+\w+|#include)', line))
            
            language = "text"
            if python_count > js_count and python_count > java_count:
                language = "python"
            elif js_count > python_count and js_count > java_count:
                language = "javascript"
            elif java_count > python_count and java_count > js_count:
                language = "java"
            
            return [(language, response)]
        
        return []

    def get_file_extension(self, language):
        """Get file extension based on programming language"""
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'java': '.java',
            'cpp': '.cpp',
            'c++': '.cpp',
            'c': '.c',
            'csharp': '.cs',
            'cs': '.cs',
            'html': '.html',
            'css': '.css',
            'php': '.php',
            'ruby': '.rb',
            'go': '.go',
            'rust': '.rs',
            'swift': '.swift',
            'kotlin': '.kt',
            'sql': '.sql',
            'bash': '.sh',
            'shell': '.sh',
            'typescript': '.ts',
            'tsx': '.tsx',
            'jsx': '.jsx'
        }
        return extensions.get(language.lower(), f'.{language.lower()}')

    async def log_code_generation(self, user_id, message, response, language, success=True, error=None):
        """Log code generation requests and outcomes"""
        if not self.bot.db:
            return
        try:
            cursor = self.bot.db.cursor()
            cursor.execute('''
                INSERT INTO code_generation_logs 
                (user_id, request_content, response_content, language, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(user_id),
                message,
                response,
                language,
                success,
                error
            ))
            self.bot.db.commit()
        except Exception as e:
            print(f"Error logging code generation: {e}")

    def filter_ai_response(self, response):
        """تصفية رد الذكاء الاصطناعي لإظهار الرد النهائي فقط وإزالة التفكير"""
        # تقسيم الرد إلى أسطر
        lines = response.split('\n')
        
        # إزالة الأسطر التي تحتوي على تفكير
        filtered_lines = []
        skip_line = False
        
        for line in lines:
            # تحقق مما إذا كانت السطر يحتوي على تفكير
            if "تفكر" in line or "تفكير" in line or "process" in line.lower() or "thinking" in line.lower():
                skip_line = True
                continue
            
            # تحقق مما إذا كانت السطر يحتوي على علامة نهاية التفكير
            if "الرد النهائي" in line or "final response" in line.lower() or "---" in line:
                skip_line = False
                continue
                
            # إذا لم نكن في وضع تخطي السطر، أضف السطر
            if not skip_line:
                filtered_lines.append(line)
        
        # إذا لم يتم العثور على رد مفلتر، أرجع الرد الأصلي
        if not filtered_lines:
            return response
            
        # دمج الأسطر المفلترة
        filtered_response = '\n'.join(filtered_lines).strip()
        
        # إذا كان الرد المفلتر فارغًا، أرجع الرد الأصلي
        if not filtered_response:
            return response
            
        return filtered_response
    
    def format_code_response(self, response):
        """Format code responses with proper syntax highlighting"""
        import re
        
        # Check if response contains code blocks
        if "```" in response:
            # Already has code blocks, return as is
            return response
        
        # Check for common programming patterns
        code_patterns = [
            r'^\s*def\s+\w+\s*\(',  # Python function definition
            r'^\s*class\s+\w+',     # Class definition
            r'^\s*import\s+\w+',    # Import statement
            r'^\s*from\s+\w+',      # From import statement
            r'^\s*function\s+\w+',  # JavaScript function
            r'^\s*const\s+\w+',     # JavaScript const
            r'^\s*let\s+\w+',       # JavaScript let
            r'^\s*var\s+\w+',       # JavaScript var
            r'^\s*public\s+class',  # Java class
            r'^\s*public\s+static', # Java static method
            r'^\s*package\s+\w+',   # Java package
            r'^\s*#include\s*<',    # C/C++ include
            r'^\s*using\s+namespace'
        ]
        
        # Check if response contains code-like patterns
        lines = response.split('\n')
        code_line_count = 0
        
        for line in lines:
            for pattern in code_patterns:
                if re.match(pattern, line):
                    code_line_count += 1
                    break
        
        # If more than 30% of lines look like code, format as code
        if len(lines) > 0 and code_line_count / len(lines) > 0.3:
            # Try to detect language based on patterns
            language = "text"
            python_count = sum(1 for line in lines if re.match(r'^\s*(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+)', line))
            js_count = sum(1 for line in lines if re.match(r'^\s*(function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+)', line))
            java_count = sum(1 for line in lines if re.match(r'^\s*(public\s+|package\s+\w+|#include)', line))
            
            if python_count > js_count and python_count > java_count:
                language = "python"
            elif js_count > python_count and js_count > java_count:
                language = "javascript"
            elif java_count > python_count and java_count > js_count:
                language = "java"
            
            return f"``{language}\n{response}\n```"
        
        return response
    
    async def update_user_stats(self, user_id, model_id, tokens_used):
        """تحديث إحصائيات المستخدم"""
        if not self.bot.db:
            return
        try:
            cursor = self.bot.db.cursor()
            cursor.execute('''
                UPDATE user_stats 
                SET commands_used = commands_used + 1,
                    tokens_used = tokens_used + ?,
                    preferred_model = ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (tokens_used, model_id, str(user_id)))
            
            # إذا لم يكن المستخدم موجوداً، أضفه
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO user_stats 
                    (user_id, username, commands_used, tokens_used, preferred_model, last_active)
                    VALUES (?, ?, 1, ?, ?, CURRENT_TIMESTAMP)
                ''', (str(user_id), f"User_{user_id}", tokens_used, model_id))
            
            self.bot.db.commit()
        except Exception as e:
            print(f"خطأ في تحديث إحصائيات المستخدم: {e}")
    
    async def log_conversation(self, user_id, message, response, model_id):
        """تسجيل المحادثة في قاعدة البيانات"""
        if not self.bot.db:
            return
        try:
            cursor = self.bot.db.cursor()
            cursor.execute('''
                INSERT INTO conversation_logs 
                (user_id, channel_id, message_content, response_content, model_used, tokens_used)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(user_id), 
                "direct_message",  # سيتم تحديث هذا لاحقاً
                message, 
                response, 
                model_id, 
                len(message) + len(response)
            ))
            self.bot.db.commit()
        except Exception as e:
            print(f"خطأ في تسجيل المحادثة: {e}")
    
    async def close_session(self):
        """إغلاق الجلسة عند إيقاف البوت"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def close(self):
        """إغلاق الجلسة عند إيقاف البوت"""
        await self.close_session()

async def setup(bot):
    cog = AIChat(bot)
    await bot.add_cog(cog)
    # التأكد من إغلاق الجلسة عند إيقاف البوت
    bot.ai_chat_cog = cog