# cogs/admin_panel.py - لوحة التحكم الإدارية
import discord
from discord.ext import commands
from discord import app_commands
import json
import sqlite3
from datetime import datetime
import typing

class AdminPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def cog_check(self, ctx):
        """التحقق من صلاحيات المشرف"""
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id in admin_ids:
            return True
        return False
    
    @commands.hybrid_group(name="admin", description="أوامر المشرف")
    async def admin(self, ctx):
        """مجموعة أوامر المشرف"""
        # التحقق من الصلاحيات
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id not in admin_ids:
            await ctx.send("⛔ ليس لديك صلاحيات كافية لاستخدام هذا الأمر", ephemeral=True)
            return
            
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⚙️ لوحة تحكم المشرف",
                description="استخدم أحد الأوامر الفرعية التالية:",
                color=0xe74c3c
            )
            embed.add_field(
                name="الأوامر المتاحة",
                value=(
                    "`/admin stats` - عرض إحصائيات النظام\n"
                    "`/admin config` - تعديل الإعدادات\n"
                    "`/admin models` - إدارة النماذج\n"
                    "`/admin set_dedicated_channel` - تعيين قناة مخصصة\n"
                    "`/admin clear_dedicated_channel` - إزالة القناة المخصصة"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
    
    @admin.command(name="stats", description="عرض إحصائيات النظام")
    async def admin_stats(self, ctx):
        """عرض إحصائيات النظام للمشرفين"""
        # التحقق من الصلاحيات
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id not in admin_ids:
            await ctx.send("⛔ ليس لديك صلاحيات كافية لاستخدام هذا الأمر", ephemeral=True)
            return
            
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_stats")
        total_users = cursor.fetchone()[0]
        
        embed = discord.Embed(
            title="📊 إحصائيات النظام",
            description=f"**وقت التشغيل:** {str(discord.utils.utcnow() - self.bot.start_time).split('.')[0]}",
            color=0x1abc9c
        )
        
        embed.add_field(name="👥 إجمالي المستخدمين", value=total_users, inline=True)
        embed.add_field(name="🖥️ السيرفرات", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="🤖 النماذج", value=len(self.bot.available_models), inline=True)
        
        await ctx.send(embed=embed)
    
    @admin.command(name="config", description="تعديل إعدادات البوت")
    async def admin_config(self, ctx):
        """تعديل إعدادات البوت"""
        # التحقق من الصلاحيات
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id not in admin_ids:
            await ctx.send("⛔ ليس لديك صلاحيات كافية لاستخدام هذا الأمر", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="⚙️ إعدادات البوت",
            description="الإعدادات الحالية:",
            color=0xf1c40f
        )
        
        for key, value in self.bot.config.items():
            if key == "admin_ids":
                value = ", ".join([str(admin_id) for admin_id in value])
            embed.add_field(name=key, value=str(value), inline=True)
        
        await ctx.send(embed=embed)
    
    @admin.command(name="models", description="إدارة النماذج")
    async def admin_models(self, ctx):
        """إدارة النماذج"""
        # التحقق من الصلاحيات
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id not in admin_ids:
            await ctx.send("⛔ ليس لديك صلاحيات كافية لاستخدام هذا الأمر", ephemeral=True)
            return
            
        # Directly call the admin_models method from ModelManager cog
        model_manager_cog = self.bot.get_cog("ModelManager")
        if model_manager_cog:
            # Call the admin_models method directly
            await model_manager_cog.admin_models(ctx)
        else:
            await ctx.send("❌ Model manager not available.", ephemeral=True)
        
    @admin.command(name="set_dedicated_channel", description="تعيين قناة مخصصة للدردشة التلقائية")
    async def set_dedicated_channel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        """تعيين قناة مخصصة للدردشة التلقائية"""
        # التحقق من الصلاحيات
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id not in admin_ids:
            await ctx.send("⛔ ليس لديك صلاحيات كافية لاستخدام هذا الأمر", ephemeral=True)
            return
            
        # إذا لم يتم تحديد قناة، استخدم القناة الحالية
        target_channel = channel if channel is not None else ctx.channel
            
        # تحديث الإعدادات
        self.bot.config["settings"]["dedicated_channel_id"] = target_channel.id
        
        # حفظ التغييرات في ملف الإعدادات
        try:
            config_path = 'config/config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, indent=4, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ تم تعيين القناة المخصصة",
                description=f"تم تعيين القناة {target_channel.mention} كقناة مخصصة للدردشة التلقائية.",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ أثناء حفظ الإعدادات: {e}", ephemeral=True)
    
    @admin.command(name="clear_dedicated_channel", description="إزالة قناة الدردشة التلقائية المخصصة")
    async def clear_dedicated_channel(self, ctx):
        """إزالة قناة الدردشة التلقائية المخصصة"""
        # التحقق من الصلاحيات
        admin_ids = self.bot.config.get("bot", {}).get("admin_ids", [])
        if ctx.author.id not in admin_ids:
            await ctx.send("⛔ ليس لديك صلاحيات كافية لاستخدام هذا الأمر", ephemeral=True)
            return
            
        # تحديث الإعدادات
        self.bot.config["settings"]["dedicated_channel_id"] = None
        
        # حفظ التغييرات في ملف الإعدادات
        try:
            config_path = 'config/config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, indent=4, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ تم إزالة القناة المخصصة",
                description="تم إزالة القناة المخصصة للدردشة التلقائية.",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ أثناء حفظ الإعدادات: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminPanel(bot))
