# utils/error_handler.py - معالج الأخطاء
import discord
from discord.ext import commands
import traceback
import logging
from datetime import datetime
import discord

class ErrorHandler:
    """معالج الأخطاء للبوت"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('AI_Discord_Bot')
    
    async def handle_command_error(self, ctx, error):
        """معالجة أخطاء الأوامر"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ الأمر المطلوب غير موجود. استخدم `!help` لعرض الأوامر المتاحة.")
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ معلمة مطلوبة مفقودة: {error.param.name}")
        
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ معلمة غير صحيحة: {error}")
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ ليس لديك الصلاحيات الكافية لتنفيذ هذا الأمر.")
        
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ البوت لا يملك الصلاحيات الكافية لتنفيذ هذا الأمر.")
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ هذا الأمر في فترة تهدئة. حاول مرة أخرى بعد {error.retry_after:.2f} ثانية.")
        
        elif isinstance(error, commands.NotOwner):
            await ctx.send("❌ هذا الأمر مخصص لمالك البوت فقط.")
        
        else:
            # تسجيل الخطأ في السجلات
            self.logger.error(f"خطأ غير معالج في الأمر {ctx.command}: {error}")
            
            # إرسال رسالة خطأ مبسطة للمستخدم
            await ctx.send("❌ حدث خطأ غير متوقع. تم تسجيل الخطأ وسيتم مراجعته.")
            
            # إرسال تفاصيل الخطأ إلى المشرفين إذا كان ذلك ممكناً
            await self.notify_admins_of_error(ctx, error)
            # Forward to webhook logger (owner server only if configured)
            try:
                logger_cog = self.bot.get_cog("WebhookLogger")
                if logger_cog and hasattr(logger_cog, "log_error"):
                    await logger_cog.log_error(error, command=str(getattr(ctx, 'command', 'unknown')))
            except Exception:
                pass
    
    async def handle_event_error(self, event_method, *args, **kwargs):
        """معالجة أخطاء الأحداث"""
        self.logger.error(f"خطأ في الحدث {event_method}")
        
        # تسجيل تفاصيل الخطأ
        traceback.print_exc()
        
        # إرسال إشعار إلى المشرفين
        await self.notify_admins_of_event_error(event_method, args, kwargs)
    
    async def notify_admins_of_error(self, ctx, error):
        """إرسال إشعار للمشرفين حول خطأ"""
        try:
            # الحصول على قائمة معرفات المشرفين
            admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
            
            if not admin_ids:
                return
            
            # إنشاء رسالة الخطأ
            error_embed = discord.Embed(
                title="🚨 خطأ في البوت",
                description=f"حدث خطأ في الأمر: `{ctx.command}`",
                color=0xff0000,
                timestamp=discord.utils.utcnow()
            )
            
            error_embed.add_field(name="المستخدم", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            error_embed.add_field(name="القناة", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
            error_embed.add_field(name="الرسالة", value=ctx.message.content[:1000], inline=False)
            error_embed.add_field(name="الخطأ", value=str(error)[:1000], inline=False)
            
            # إرسال الإشعار إلى المشرفين
            for admin_id in admin_ids:
                try:
                    admin = await self.bot.fetch_user(admin_id)
                    if admin:
                        await admin.send(embed=error_embed)
                except:
                    pass  # تجاهل الأخطاء في إرسال الرسائل للمشرفين
        except:
            pass  # تجاهل أي أخطاء في إرسال الإشعارات
    
    async def notify_admins_of_event_error(self, event_method, args, kwargs):
        """إرسال إشعار للمشرفين حول خطأ في الحدث"""
        try:
            # الحصول على قائمة معرفات المشرفين
            admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
            
            if not admin_ids:
                return
            
            # إنشاء رسالة الخطأ
            error_embed = discord.Embed(
                title="🚨 خطأ في حدث البوت",
                description=f"حدث خطأ في الحدث: `{event_method}`",
                color=0xff0000,
                timestamp=discord.utils.utcnow()
            )
            
            error_embed.add_field(name="الوسائط", value=str(args)[:1000], inline=False)
            error_embed.add_field(name="الوسائط المفتاحية", value=str(kwargs)[:1000], inline=False)
            
            # إرسال الإشعار إلى المشرفين
            for admin_id in admin_ids:
                try:
                    admin = await self.bot.fetch_user(admin_id)
                    if admin:
                        await admin.send(embed=error_embed)
                except:
                    pass  # تجاهل الأخطاء في إرسال الرسائل للمشرفين
        except:
            pass  # تجاهل أي أخطاء في إرسال الإشعارات

async def setup_error_handler(bot):
    """إعداد معالج الأخطاء للبوت"""
    error_handler = ErrorHandler(bot)
    
    # تسجيل معالج الأخطاء
    @bot.event
    async def on_command_error(ctx, error):
        await error_handler.handle_command_error(ctx, error)
    
    # يمكن إضافة معالجات أخرى للأحداث حسب الحاجة
    return error_handler
