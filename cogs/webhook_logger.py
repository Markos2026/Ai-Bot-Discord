# cogs/webhook_logger.py - نظام الويب هوك
import discord
from discord.ext import commands
import json
import aiohttp
from datetime import datetime

class WebhookLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhooks = {}
        self.load_webhooks()
    
    def load_webhooks(self):
        """تحميل إعدادات الويب هوك"""
        try:
            with open('config/webhooks.json', 'r', encoding='utf-8') as f:
                self.webhooks = json.load(f)
        except FileNotFoundError:
            self.webhooks = {
                "log_webhook": "",
                "error_webhook": "",
                "stats_webhook": "",
                "event_webhook": "",  # New webhook for admin events
                "custom_webhooks": {}
            }
            self.save_webhooks()
        # Ensure new field exists
        if "custom_webhooks" not in self.webhooks:
            self.webhooks["custom_webhooks"] = {}
            self.save_webhooks()
    
    def save_webhooks(self):
        """حفظ إعدادات الويب هوك"""
        with open('config/webhooks.json', 'w', encoding='utf-8') as f:
            json.dump(self.webhooks, f, indent=4, ensure_ascii=False)
    
    async def send_log(self, webhook_type, embed, guild_id: int | None = None):
        """إرسال سجل إلى الويب هوك مع قيد خادم المالك إن وُجد."""
        webhook_url = self.webhooks.get(f"{webhook_type}_webhook")
        if not webhook_url:
            return

        owner_server_id = self.bot.config.get("bot", {}).get("owner_server_id")
        if owner_server_id is not None:
            try:
                if guild_id is None or int(guild_id) != int(owner_server_id):
                    return
                embed.set_footer(text=f"Developer server only • {owner_server_id}")
            except Exception:
                return
        
        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                await webhook.send(embed=embed)
        except Exception as e:
            print(f"خطأ في إرسال الويب هوك: {e}")

    async def _send_to_url(self, url: str, embed: discord.Embed):
        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(url, session=session)
                await webhook.send(embed=embed)
        except Exception as e:
            raise e
    
    async def log_command(self, ctx):
        """تسجيل استخدام الأمر"""
        embed = discord.Embed(
            title="📝 استخدام أمر",
            description=f"تم استخدام الأمر: `{ctx.command.name}`",
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="المستخدم", value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="القناة", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
        
        gid = ctx.guild.id if ctx.guild else None
        if ctx.guild:
            embed.add_field(name="السيرفر", value=f"{ctx.guild} ({ctx.guild.id})", inline=True)
        
        await self.send_log("log", embed, guild_id=gid)
    
    async def log_error(self, error, command=None):
        """تسجيل خطأ"""
        embed = discord.Embed(
            title="❌ خطأ",
            description=f"```{str(error)}```",
            color=0xe74c3c,
            timestamp=discord.utils.utcnow()
        )
        
        if command:
            embed.add_field(name="الأمر", value=command, inline=True)
        
        await self.send_log("error", embed, guild_id=None)
    
    async def log_admin_event(self, event_type, user, details=""):
        """تسجيل أحداث الإدارة"""
        embed = discord.Embed(
            title=f"⚙️ {event_type}",
            description=details,
            color=0x9b59b6,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="المستخدم", value=f"{user} ({user.id})", inline=True)
        
        await self.send_log("event", embed, guild_id=(user.guild.id if hasattr(user, 'guild') and user.guild else None))
    
    async def log_model_event(self, event_type, user, model_name, details=""):
        """تسجيل أحداث النماذج"""
        embed = discord.Embed(
            title=f"🤖 {event_type}",
            description=f"**النموذج:** {model_name}\n{details}",
            color=0xf1c40f,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="المستخدم", value=f"{user} ({user.id})", inline=True)
        
        await self.send_log("event", embed, guild_id=(user.guild.id if hasattr(user, 'guild') and user.guild else None))
    
    async def log_stats(self, stats):
        """تسجيل إحصائيات"""
        embed = discord.Embed(
            title="📊 تحديث الإحصائيات",
            color=0xf1c40f,
            timestamp=discord.utils.utcnow()
        )
        
        for key, value in stats.items():
            embed.add_field(name=key, value=value, inline=True)
        
        await self.send_log("stats", embed, guild_id=None)
    
    @commands.hybrid_group(name="webhook", description="إدارة الويب هوك")
    @commands.has_permissions(administrator=True)
    async def webhook(self, ctx):
        """مجموعة أوامر الويب هوك"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🔗 إدارة الويب هوك",
                description=("استخدم الأوامر: add / setup / delete / list / test / test_all"),
                color=0x9b59b6
            )
            embed.add_field(
                name="الأوامر المتاحة",
                value=(
                    "`/webhook add` - إضافة ويبهوك مخصص\n"
                    "`/webhook setup` - إعداد سريع\n"
                    "`/webhook delete` - حذف نوع أو اسم\n"
                    "`/webhook list` - عرض الويب هوك المعينة\n"
                    "`/webhook test` - اختبار ويبهوك محدد\n"
                    "`/webhook test_all` - اختبار جميع الويبهوكس"
                ),
                inline=False
            )
            await ctx.send(embed=embed)

    @webhook.command(name="add", description="إضافة ويبهوك مخصص")
    async def webhook_add(self, ctx: commands.Context, name: str, webhook_url: str, type: str | None = None):
        custom = self.webhooks.get("custom_webhooks", {})
        if name in custom:
            await ctx.send("⚠️ يوجد ويبهوك بهذا الاسم مسبقاً.")
            return
        if type and type not in ["log", "error", "stats", "event"]:
            await ctx.send("⚠️ النوع غير صالح. الأنواع: log, error, stats, event")
            return
        custom[name] = {"url": webhook_url, "type": type or "custom"}
        self.webhooks["custom_webhooks"] = custom
        self.save_webhooks()
        await ctx.send(f"✅ تم إضافة الويبهوك `{name}` بنجاح")

    @webhook.command(name="setup", description="إعداد سريع لأنواع الويبهوك")
    async def webhook_setup(self, ctx: commands.Context, log_url: str | None = None, error_url: str | None = None, stats_url: str | None = None, event_url: str | None = None):
        changed = []
        if log_url:
            self.webhooks["log_webhook"] = log_url
            changed.append("log")
        if error_url:
            self.webhooks["error_webhook"] = error_url
            changed.append("error")
        if stats_url:
            self.webhooks["stats_webhook"] = stats_url
            changed.append("stats")
        if event_url is not None:
            self.webhooks["event_webhook"] = event_url
            changed.append("event")
        if not changed:
            await ctx.send("ℹ️ لم يتم تمرير أي روابط. استخدم المعاملات المتاحة.")
            return
        self.save_webhooks()
        await ctx.send("✅ تم تحديث: " + ", ".join(changed))
    
    @webhook.command(name="list", description="عرض الويب هوك المعينة")
    async def webhook_list(self, ctx):
        """عرض الويب هوك المعينة"""
        embed = discord.Embed(
            title="🔗 الويب هوك المعينة",
            color=0x9b59b6
        )
        for key in ["log_webhook", "error_webhook", "stats_webhook", "event_webhook"]:
            url = self.webhooks.get(key, "")
            status = "✅ معين" if url else "❌ غير معين"
            embed.add_field(name=key, value=status, inline=False)
        custom = self.webhooks.get("custom_webhooks", {})
        if custom:
            for name, info in custom.items():
                status = "✅" if info.get("url") else "❌"
                embed.add_field(name=f"custom:{name}", value=f"{status} ({info.get('type','custom')})", inline=False)
        else:
            embed.add_field(name="custom_webhooks", value="لا توجد ويبهوكس مخصصة", inline=False)
        await ctx.send(embed=embed)
    
    @webhook.command(name="test", description="اختبار الويب هوك")
    async def webhook_test(self, ctx: commands.Context, target: str):
        """اختبار نوع (log/error/stats/event) أو اسم مخصص"""
        url = None
        if target in ["log", "error", "stats", "event"]:
            url = self.webhooks.get(f"{target}_webhook")
        else:
            url = self.webhooks.get("custom_webhooks", {}).get(target, {}).get("url")
        if not url:
            await ctx.send("⚠️ لم يتم العثور على هدف بهذا الاسم أو النوع.")
            return
        embed = discord.Embed(
            title="🧪 اختبار الويبهوك",
            description=f"اختبار إرسال إلى: {target}",
            color=0x2ecc71,
            timestamp=discord.utils.utcnow()
        )
        try:
            await self._send_to_url(url, embed)
            await ctx.send(f"✅ تم الاختبار بنجاح: {target}")
        except Exception as e:
            await ctx.send(f"❌ فشل الاختبار: {e}")

    @webhook.command(name="test_all", description="اختبار جميع الويبهوكس")
    async def webhook_test_all(self, ctx: commands.Context):
        targets = []
        for key in ["log_webhook", "error_webhook", "stats_webhook", "event_webhook"]:
            if self.webhooks.get(key):
                targets.append((key, self.webhooks[key]))
        for name, info in self.webhooks.get("custom_webhooks", {}).items():
            if info.get("url"):
                targets.append((f"custom:{name}", info["url"]))
        if not targets:
            await ctx.send("ℹ️ لا توجد ويبهوكس لإختبارها.")
            return
        embed = discord.Embed(
            title="🧪 اختبار جماعي",
            description=f"عدد الأهداف: {len(targets)}",
            color=0x2ecc71,
            timestamp=discord.utils.utcnow()
        )
        successes = 0
        for label, url in targets:
            try:
                await self._send_to_url(url, embed)
                successes += 1
            except Exception:
                pass
        await ctx.send(f"تم إرسال الاختبار إلى {successes}/{len(targets)} ويبهوك")

    @webhook.command(name="delete", description="حذف نوع أو اسم ويبهوك")
    async def webhook_delete(self, ctx: commands.Context, target: str):
        if target in ["log", "error", "stats", "event"]:
            key = f"{target}_webhook"
            existed = bool(self.webhooks.get(key))
            self.webhooks[key] = ""
            self.save_webhooks()
            await ctx.send("✅ تم حذف الرابط" if existed else "ℹ️ لم يكن هناك رابط معيّن")
            return
        custom = self.webhooks.get("custom_webhooks", {})
        if target in custom:
            del custom[target]
            self.webhooks["custom_webhooks"] = custom
            self.save_webhooks()
            await ctx.send(f"✅ تم حذف الويبهوك `{target}`")
        else:
            await ctx.send("⚠️ لم يتم العثور على ويبهوك بهذا الاسم")

async def setup(bot):
    await bot.add_cog(WebhookLogger(bot))
