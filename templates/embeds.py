# templates/embeds.py - قوالب Embeds
import discord
from datetime import datetime

class EmbedTemplates:
    """قوالب Embeds للبوت"""
    
    @staticmethod
    def create_success_embed(title, description="", fields=None):
        """إنشاء embed للرسائل الناجحة"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x00ff00  # أخضر
        )
        embed.timestamp = datetime.now()
        
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        
        return embed
    
    @staticmethod
    def create_error_embed(title, description="", fields=None):
        """إنشاء embed للرسائل الخطأ"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=0xff0000  # أحمر
        )
        embed.timestamp = datetime.now()
        
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        
        return embed
    
    @staticmethod
    def create_info_embed(title, description="", fields=None):
        """إنشاء embed للرسائل المعلوماتية"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x3498db  # أزرق
        )
        embed.timestamp = datetime.now()
        
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        
        return embed
    
    @staticmethod
    def create_warning_embed(title, description="", fields=None):
        """إنشاء embed للرسائل التحذيرية"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=0xf1c40f  # أصفر
        )
        embed.timestamp = datetime.now()
        
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        
        return embed
    
    @staticmethod
    def create_model_embed(model_id, model_info):
        """إنشاء embed لنموذج معين"""
        status = "🟢 مفعل" if model_info.get('enabled', True) else "🔴 معطل"
        
        embed = discord.Embed(
            title=f"🤖 {model_info['display_name']}",
            color=0x9b59b6  # بنفسجي
        )
        
        embed.add_field(name="الحالة", value=status, inline=True)
        embed.add_field(name="المعرف", value=f"`{model_id}`", inline=True)
        
        if 'provider' in model_info:
            embed.add_field(name="المزود", value=model_info['provider'], inline=True)
        
        if 'context_length' in model_info:
            embed.add_field(name="طول السياق", value=f"{model_info['context_length']} رمز", inline=True)
        
        if 'is_free' in model_info:
            price = "مجاني" if model_info['is_free'] else "مدفوع"
            embed.add_field(name="السعر", value=price, inline=True)
        
        embed.timestamp = datetime.now()
        return embed
    
    @staticmethod
    def create_user_stats_embed(user, stats):
        """إنشاء embed لإحصائيات المستخدم"""
        embed = discord.Embed(
            title=f"📊 إحصائيات {user.display_name}",
            color=0x3498db
        )
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        
        embed.add_field(name="💬 إجمالي الرسائل", value=stats.get('total_messages', 0), inline=True)
        embed.add_field(name="⌨️ الأوامر المستخدمة", value=stats.get('commands_used', 0), inline=True)
        
        if stats.get('preferred_model'):
            embed.add_field(name="🤖 النموذج المفضل", value=stats['preferred_model'], inline=True)
        
        embed.add_field(name="🔢 التوكنز المستخدمة", value=stats.get('tokens_used', 0), inline=True)
        
        if stats.get('last_active'):
            embed.add_field(name="⏱️ آخر نشاط", value=stats['last_active'], inline=True)
        
        embed.timestamp = datetime.now()
        return embed
    
    @staticmethod
    def create_bot_stats_embed(bot, stats):
        """إنشاء embed لإحصائيات البوت"""
        embed = discord.Embed(
            title="📊 إحصائيات البوت",
            color=0xf1c40f
        )
        
        uptime = datetime.now() - bot.start_time
        embed.add_field(name="⏰ وقت التشغيل", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="👥 إجمالي المستخدمين", value=stats.get('total_users', 0), inline=True)
        embed.add_field(name="💬 إجمالي الرسائل", value=stats.get('total_messages', 0), inline=True)
        embed.add_field(name="🖥️ السيرفرات", value=len(bot.guilds), inline=True)
        embed.add_field(name="⚡ البينج", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🤖 النماذج", value=len(bot.available_models), inline=True)
        
        embed.timestamp = datetime.now()
        return embed