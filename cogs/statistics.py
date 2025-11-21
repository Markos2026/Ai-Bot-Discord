# cogs/statistics.py - نظام الإحصائيات المتكامل
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from datetime import datetime

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(
        name="mystats",
        description="عرض إحصائياتك الشخصية"
    )
    async def mystats(self, ctx: commands.Context):
        """عرض إحصائيات المستخدم الشخصية"""
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT * FROM user_stats WHERE user_id = ?", (str(ctx.author.id),))
        user_data = cursor.fetchone()
        
        if not user_data:
            await ctx.send("⚠️ لم يتم العثور على إحصائيات لك بعد. جرب استخدام البوت أولاً.")
            return
        
        embed = discord.Embed(
            title="📊 إحصائياتك الشخصية",
            color=0x3498db
        )
        
        embed.add_field(name="💬 إجمالي الرسائل", value=user_data['total_messages'], inline=True)
        embed.add_field(name="⌨️ الأوامر المستخدمة", value=user_data['commands_used'], inline=True)
        
        if user_data['preferred_model']:
            embed.add_field(name="🤖 النموذج المفضل", value=user_data['preferred_model'], inline=True)
        
        embed.add_field(name="🔢 التوكنز المستخدمة", value=user_data['tokens_used'], inline=True)
        embed.add_field(name="⏱️ آخر نشاط", value=user_data['last_active'], inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="botstats",
        description="عرض إحصائيات البوت العامة"
    )
    async def botstats(self, ctx: commands.Context):
        """عرض إحصائيات البوت العامة"""
        cursor = self.bot.db.cursor()
        
        # إجمالي المستخدمين
        cursor.execute("SELECT COUNT(*) FROM user_stats")
        total_users = cursor.fetchone()[0]
        
        # إجمالي الرسائل
        cursor.execute("SELECT COUNT(*) FROM conversation_logs")
        total_messages = cursor.fetchone()[0]
        
        # المستخدمين النشطين اليوم
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_stats WHERE DATE(last_active) = DATE('now')")
        active_users_today = cursor.fetchone()[0]
        
        embed = discord.Embed(
            title="📊 إحصائيات البوت",
            description=f"**وقت التشغيل:** {str(datetime.now() - self.bot.start_time).split('.')[0]}",
            color=0xf1c40f
        )
        
        embed.add_field(name="👥 إجمالي المستخدمين", value=total_users, inline=True)
        embed.add_field(name="💬 إجمالي الرسائل", value=total_messages, inline=True)
        embed.add_field(name="🔄 المستخدمين النشطين اليوم", value=active_users_today, inline=True)
        embed.add_field(name="🖥️ السيرفرات", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="⚡ البينج", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🤖 النماذج", value=len(self.bot.available_models), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Statistics(bot))