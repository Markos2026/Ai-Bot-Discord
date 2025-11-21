# main.py - البوت المتكامل بدون أخطاء
import discord
from discord.ext import commands
import asyncio
import os
import sqlite3
import logging
import aiohttp
from datetime import datetime
import json

# Advanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('AI_Discord_Bot')

class AIDiscordBot(commands.Bot):
    def __init__(self):
        # إعدادات متقدمة للأوامر الهجينة
        intents = discord.Intents.all()
        
        # تهيئة البوت بدون دالة get_prefix مخصصة أولاً
        super().__init__(
            command_prefix="!",  # سيتم تحديثه لاحقاً
            intents=intents,
            help_command=None,
            chunk_guilds_at_startup=False,
            status=discord.Status.dnd,
            activity=discord.Streaming(
                name="Dev ELMINYAWE",
                url="https://www.twitch.tv/dev_elminyawe"
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False,
                users=True,
                replied_user=True
            )
        )
        
        # استخدم وقت UTC الواعي لتجنب أخطاء طرح الوقت
        self.start_time = discord.utils.utcnow()
        self.session = None
        self.db = None
        self.config = {}
        self.available_models = {}
        
        # الحصول على المسار الأساسي للتطبيق
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # تحميل الإعدادات
        self.load_config()
        
        # تحديث البريفكس بعد تحميل الإعدادات
        self.command_prefix = self._get_prefix
    
    def _get_prefix(self, bot, message):
        """دعم الأوامر الهجينة (بريفكس وسلاش)"""
        prefix = self.config.get("bot", {}).get("prefix", "!") if hasattr(self, 'config') and "bot" in self.config else "!"
        prefixes = [prefix, "/"]
        return commands.when_mentioned_or(*prefixes)(bot, message)
        
    def load_config(self):
        """تحميل الإعدادات من الملفات"""
        try:
            config_path = os.path.join(self.base_path, 'config', 'config.json')
            models_config_path = os.path.join(self.base_path, 'config', 'models_config.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # دعم التنسيق الجديد والقديم
                if 'bot' in config_data:
                    self.config = config_data
                else:
                    # تحويل التنسيق القديم إلى الجديد
                    self.config = {
                        "bot": {
                            "name": "AI Discord Bot",
                            "version": "2.0.0",
                            "prefix": config_data.get("prefix", "!"),
                            "admin_ids": config_data.get("admin_ids", []),
                            "support_server": "",
                            "owner_server_id": None  # Add owner server ID
                        },
                        "settings": {
                            "max_message_length": config_data.get("max_message_length", 2000),
                            "default_model": config_data.get("default_model", "tngtech/deepseek-r1t2-chimera:free"),
                            "enable_dm": True,
                            "enable_hybrid_commands": True,
                            "auto_update_stats": True
                        },
                        "performance": {
                            "max_concurrent_requests": 5,
                            "request_timeout": 30,
                            "cache_responses": True,
                            "cleanup_interval": 300
                        },
                        "log_channel": config_data.get("log_channel", None)
                    }
            
            with open(models_config_path, 'r', encoding='utf-8') as f:
                self.available_models = json.load(f)
            logger.info("✅ Settings loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading settings: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """الإعدادات الافتراضية"""
        return {
            "bot": {
                "name": "AI Discord Bot",
                "version": "2.0.0",
                "prefix": "!",
                "admin_ids": [],
                "support_server": "",
                "owner_server_id": None  # Add owner server ID
            },
            "settings": {
                "max_message_length": 2000,
                "default_model": "tngtech/deepseek-r1t2-chimera:free",
                "enable_dm": True,
                "enable_hybrid_commands": True,
                "auto_update_stats": True
            },
            "performance": {
                "max_concurrent_requests": 5,
                "request_timeout": 30,
                "cache_responses": True,
                "cleanup_interval": 300
            },
            "log_channel": None
        }
    
    @commands.command(name="y31")
    async def set_owner_server(self, ctx):
        """Set the owner server ID - can only be used by bot owner"""
        # Check if user is bot owner
        bot_owner_id = self.config.get("bot", {}).get("admin_ids", [None])[0] if self.config.get("bot", {}).get("admin_ids") else None
        if ctx.author.id != bot_owner_id:
            await ctx.send("❌ Only the bot owner can use this command.", ephemeral=True)
            return
        
        # Prompt for owner server ID
        await ctx.send("Please provide the server ID for your developer server:")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.wait_for('message', check=check, timeout=60.0)
            server_id = int(msg.content)
            
            # Validate server ID
            guild = self.get_guild(server_id)
            if not guild:
                await ctx.send("❌ Invalid server ID or bot is not in that server.")
                return
            
            # Update config
            self.config["bot"]["owner_server_id"] = server_id
            self.save_config()
            
            await ctx.send(f"✅ Owner server ID set to {server_id} ({guild.name})")
        except ValueError:
            await ctx.send("❌ Invalid server ID format. Please provide a valid number.")
        except asyncio.TimeoutError:
            await ctx.send("❌ Command timed out. Please try again.")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config_path = os.path.join(self.base_path, 'config', 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    async def setup_hook(self):
        """إعداد البوت المتكامل"""
        logger.info("🚀 Starting bot setup...")
        
        try:
            # تهيئة الجلسة
            self.session = aiohttp.ClientSession()
            
            # تهيئة قاعدة البيانات
            await self.initialize_database()
            
            # تحميل جميع الإضافات
            await self.load_all_cogs()
            
            # مزامنة الأوامر
            await self.tree.sync()
            
            # بدء الخدمات الخلفية
            await self.start_background_tasks()

            # تفعيل ملتقط الأخطاء العام
            try:
                from utils.error_handler import setup_error_handler
                await setup_error_handler(self)
            except Exception as eh:
                logger.error(f"Error enabling global error handler: {eh}")
            
            logger.info("✅ Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in bot setup: {e}")
            raise
    
    async def initialize_database(self):
        """تهيئة قاعدة البيانات المتكاملة"""
        try:
            database_path = os.path.join(self.base_path, 'database', 'models.sqlite')
            self.db = sqlite3.connect(database_path, check_same_thread=False)
            self.db.row_factory = sqlite3.Row
            
            # إنشاء الجداول
            await self.create_database_tables()
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            raise
    
    async def create_database_tables(self):
        """إنشاء جميع الجداول اللازمة"""
        if self.db is None:
            return
            
        cursor = self.db.cursor()
        
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
        
        self.db.commit()
    
    async def load_all_cogs(self):
        """تحميل جميع الإضافات"""
        cogs = [
            'cogs.hybrid_commands',
            'cogs.ai_chat',
            'cogs.model_manager',
            'cogs.admin_panel',
            'cogs.statistics',
            'cogs.webhook_logger',
            'cogs.dashboard',  # New dashboard cog
            'cogs.enhanced_stats',  # New enhanced stats cog
            'cogs.status_manager'  # Auto status posting and updates
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"✅ Loaded {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load {cog}: {e}")
    
    async def start_background_tasks(self):
        """بدء المهام الخلفية"""
        # تحديث الإحصائيات كل دقيقة
        self.loop.create_task(self.periodic_statistics_update())
        
        # تنظيف البيانات المؤقتة كل 5 دقائق
        self.loop.create_task(self.periodic_cleanup())
        
        logger.info("✅ Background tasks started")
    
    async def periodic_statistics_update(self):
        """تحديث الإحصائيات الدوري"""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                # تحديث الإحصائيات الحية
                await self.update_live_statistics()
                await asyncio.sleep(60)  # كل دقيقة
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                await asyncio.sleep(30)
    
    async def periodic_cleanup(self):
        """تنظيف البيانات الدوري"""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.cleanup_old_data()
                await asyncio.sleep(300)  # كل 5 دقائق
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                await asyncio.sleep(300)
    
    async def on_ready(self):
        """حدث اكتمال تحميل البوت"""
        logger.info(f'🎯 Bot {self.user} is now running!')
        logger.info(f'📊 Connected to {len(self.guilds)} servers')
        logger.info(f'⚡ {len(self.tree.get_commands())} commands ready')
        logger.info(f'🔧 Hybrid commands enabled (prefix + slash)')
        
        # إرسال إشعار بدء التشغيل
        await self.send_startup_notification()
    
    async def send_startup_notification(self):
        """إرسال إشعار بدء التشغيل"""
        try:
            embed = discord.Embed(
                title="🚀 Bot is now running successfully",
                description=f"**Started at:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                color=0x00ff00
            )
            embed.add_field(name="Servers", value=len(self.guilds), inline=True)
            embed.add_field(name="Commands", value=len(self.tree.get_commands()), inline=True)
            embed.add_field(name="Models", value=len(self.available_models), inline=True)
            
            # إرسال إلى قناة محددة إذا كانت متوفرة
            log_channel_id = self.config.get("log_channel")
            if log_channel_id:
                channel = self.get_channel(log_channel_id)
                # التحقق من أن القناة قابلة للإرسال
                if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.Thread)):
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")
    
    async def on_message(self, message):
        """معالجة جميع الرسائل"""
        # تجاهل رسائل البوت نفسه
        if message.author == self.user:
            return
        
        # التحقق مما إذا كانت الرسالة في القناة المخصصة
        dedicated_channel_id = self.config.get("settings", {}).get("dedicated_channel_id")
        if dedicated_channel_id and message.channel.id == dedicated_channel_id:
            # معالجة الرسالة كطلب ذكاء اصطناعي تلقائي
            async with message.channel.typing():
                try:
                    response = await self.generate_ai_response(message.content, message.author.id)
                    
                    # التأكد من أن الرد هو سلسلة نصية
                    response_str = str(response) if response is not None else "Sorry, I couldn't generate a response."
                    
                    # تقسيم الرد إذا كان طويلاً
                    max_length = self.config.get("settings", {}).get("max_message_length", 2000)
                    if len(response_str) > max_length:
                        # تقسيم الرد إلى أجزاء
                        for i in range(0, len(response_str), max_length):
                            await message.channel.send(response_str[i:i+max_length])
                    else:
                        await message.channel.send(response_str)
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    await message.channel.send("Sorry, an error occurred while generating a response. Please try again later.")
            return
        
        # معالجة الرسائل المباشرة تلقائياً
        if isinstance(message.channel, discord.DMChannel) and self.config.get("settings", {}).get("enable_dm", True):
            # إظهار أن البوت يعمل على الرد
            async with message.channel.typing():
                # التحقق مما إذا كانت الرسالة هي "كيف حالك"
                if message.content.strip() == "كيف حالك":
                    # إرسال رد مباشر باللغة العربية
                    await message.author.send("أنا بخير، شكرًا! كيف يمكنني مساعدتك اليوم؟ 😊")
                    return
                
                # استخدام النموذج الافتراضي لتوليد رد ديناميكي
                try:
                    response = await self.generate_ai_response(message.content, message.author.id)
                    
                    # التأكد من أن الرد هو سلسلة نصية
                    response_str = str(response) if response is not None else "Sorry, I couldn't generate a response."
                    
                    # تقسيم الرد إذا كان طويلاً
                    max_length = self.config.get("settings", {}).get("max_message_length", 2000)
                    if len(response_str) > max_length:
                        # تقسيم الرد إلى أجزاء
                        for i in range(0, len(response_str), max_length):
                            await message.author.send(response_str[i:i+max_length])
                    else:
                        await message.author.send(response_str)
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    await message.author.send("Sorry, an error occurred while generating a response. Please try again later.")
            return
        
        # تحديث إحصائيات المستخدم
        await self.update_user_stats(message.author)
        
        # معالجة الأوامر
        await self.process_commands(message)
    
    async def generate_ai_response(self, message, user_id):
        """توليد رد من الذكاء الاصطناعي باستخدام OpenRouter"""
        # هذه الدالة تستخدم الـ cog الخاص بالدردشة
        ai_chat_cog = self.get_cog("AIChat")
        # التحقق من أن الكائن موجود وأن له طريقة generate_response
        if ai_chat_cog is not None:
            # استخدام getattr للوصول إلى generate_response بطريقة آمنة
            generate_response_method = getattr(ai_chat_cog, 'generate_response', None)
            if generate_response_method is not None and callable(generate_response_method):
                # الحصول على النموذج الافتراضي من الإعدادات
                default_model = self.config.get("settings", {}).get("default_model", "tngtech/deepseek-r1t2-chimera:free")
                import inspect
                if inspect.iscoroutinefunction(generate_response_method):
                    return await generate_response_method(message, user_id, default_model)
                else:
                    return generate_response_method(message, user_id, default_model)
        return "Sorry, the chat system is currently unavailable."
    
    async def update_user_stats(self, user):
        """تحديث إحصائيات المستخدم"""
        if self.db is None:
            return
            
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_stats 
                (user_id, username, last_active, total_messages) 
                VALUES (?, ?, CURRENT_TIMESTAMP, COALESCE((SELECT total_messages FROM user_stats WHERE user_id = ?), 0) + 1)
            ''', (str(user.id), str(user), str(user.id)))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
    
    async def update_live_statistics(self):
        """تحديث الإحصائيات الحية"""
        if self.db is None:
            return
            
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_stats 
                (stat_date, total_messages, active_users, uptime_seconds)
                VALUES (DATE('now'), 
                (SELECT COUNT(*) FROM conversation_logs WHERE DATE(timestamp) = DATE('now')),
                (SELECT COUNT(DISTINCT user_id) FROM user_stats WHERE DATE(last_active) = DATE('now')),
                ?)
            ''', (int((discord.utils.utcnow() - self.start_time).total_seconds()),))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error updating live statistics: {e}")
            # Forward error to webhook without blocking
            try:
                logger_cog = self.get_cog("WebhookLogger")
                if logger_cog and hasattr(logger_cog, "log_error"):
                    await logger_cog.log_error(e, command="update_live_statistics")
            except Exception:
                pass
    
    async def cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        if self.db is None:
            return
            
        try:
            cursor = self.db.cursor()
            # حذف سجلات المحادثات الأ older من 30 يوم
            cursor.execute('DELETE FROM conversation_logs WHERE timestamp < datetime("now", "-30 days")')
            self.db.commit()
            logger.info("✅ Old data cleaned up")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    async def close(self):
        """إيقاف البوت بشكل آمن"""
        logger.info("🛑 Shutting down bot...")
        
        # إغلاق جلسة AI Chat إذا كانت موجودة
        ai_chat_cog = self.get_cog("AIChat")
        if ai_chat_cog:
            # التحقق من وجود طريقة لإغلاق الجلسة في cog
            try:
                # استخدام getattr للوصول إلى close_session بطريقة آمنة
                close_method = getattr(ai_chat_cog, 'close_session', None)
                if close_method and callable(close_method):
                    # التحقق من أن الطريقة قابلة للانتظار قبل استخدام await
                    import inspect
                    if inspect.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
            except Exception as e:
                logger.error(f"Error closing AI Chat session: {e}")
                pass
        
        if self.session:
            await self.session.close()
        if self.db:
            self.db.close()
        
        await super().close()
        logger.info("✅ Bot shutdown completed successfully")

# تشغيل البوت
if __name__ == "__main__":
    bot = AIDiscordBot()
    
    # استخدام التوكن مباشرة
    token = "MTQzMjg1NTM2MTM1Nzg3MzIzMg.GjpwPy.yUblEJt-M5uN-jPo_m56USyRBqBGQu9X8R7ecI"
    
    # تشغيل البوت
    bot.run(token)
