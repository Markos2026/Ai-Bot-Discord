import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

class DashboardView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.bot = bot
        self.user = user
        # قائمة إدارة مبسطة داخل اللوحة
        self.add_item(ManageMenuSelect(bot=self.bot, user=self.user))
    
    @discord.ui.button(label="🤖 Bot Status", style=discord.ButtonStyle.primary, custom_id="bot_status")
    async def bot_status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Bot Status",
            description="Current bot status and performance metrics",
            color=0x3498db
        )
        
        # Get bot stats
        total_users = len(self.bot.users)
        total_servers = len(self.bot.guilds)
        uptime = discord.utils.utcnow() - self.bot.start_time
        
        embed.add_field(name="👥 Users", value=total_users, inline=True)
        embed.add_field(name="🖥️ Servers", value=total_servers, inline=True)
        embed.add_field(name="⏰ Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="🤖 Models", value=len(self.bot.available_models), inline=True)
        embed.add_field(name="⚡ Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="💾 Version", value="v2.0.0", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📈 Statistics", style=discord.ButtonStyle.success, custom_id="statistics")
    async def statistics_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
        
        # Get statistics from database
        if not self.bot.db:
            await interaction.response.send_message("❌ Database not available.", ephemeral=True)
            return
        
        try:
            cursor = self.bot.db.cursor()
            
            # Get user stats
            cursor.execute("SELECT COUNT(*) FROM user_stats")
            total_users = cursor.fetchone()[0]
            
            # Get conversation stats
            cursor.execute("SELECT COUNT(*) FROM conversation_logs")
            total_conversations = cursor.fetchone()[0]
            
            # Get code generation stats
            cursor.execute("SELECT COUNT(*) FROM code_generation_logs")
            total_code_generations = cursor.fetchone()[0]
            
            # Get recent activity (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM conversation_logs 
                WHERE timestamp > datetime('now', '-1 day')
            """)
            recent_conversations = cursor.fetchone()[0]
            
            embed = discord.Embed(
                title="📈 Bot Statistics",
                description="Comprehensive statistics and analytics",
                color=0x2ecc71
            )
            
            embed.add_field(name="👥 Total Users", value=total_users, inline=True)
            embed.add_field(name="💬 Total Conversations", value=total_conversations, inline=True)
            embed.add_field(name="💻 Code Generations", value=total_code_generations, inline=True)
            embed.add_field(name="📅 Recent Activity (24h)", value=recent_conversations, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving statistics: {e}", ephemeral=True)
    
    @discord.ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary, custom_id="settings")
    async def settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
        # Simplified: settings moved to admin panel
        await interaction.response.send_message("ℹ️ تم تبسيط اللوحة. الإعدادات متاحة في لوحة الإدارة فقط.", ephemeral=True)
    
    @discord.ui.button(label="📋 Models", style=discord.ButtonStyle.danger, custom_id="models")
    async def models_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
        # Simplified: models management moved to admin panel
        await interaction.response.send_message("ℹ️ إدارة النماذج أصبحت عبر لوحة الإدارة فقط.", ephemeral=True)

class SettingsView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
    
    @discord.ui.button(label="🔤 Change Prefix", style=discord.ButtonStyle.primary)
    async def change_prefix_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
        
        # Show prefix change modal
        modal = PrefixModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🤖 Set Default Model", style=discord.ButtonStyle.secondary)
    async def set_default_model_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
        
        # Show model selection
        if not self.bot.available_models:
            await interaction.response.send_message("❌ No models available.", ephemeral=True)
            return
        
        view = SetDefaultModelView(self.bot, self.user, self.bot.available_models)
        embed = discord.Embed(
            title="⭐ Set Default Model",
            description="Select a model to set as default:",
            color=0xf1c40f
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PrefixModal(discord.ui.Modal, title="Change Bot Prefix"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.prefix = discord.ui.TextInput(
            label="New Prefix",
            placeholder="Enter new prefix...",
            style=discord.TextStyle.short,
            required=True,
            max_length=5
        )
        self.add_item(self.prefix)
    
    async def on_submit(self, interaction: discord.Interaction):
        new_prefix = self.prefix.value
        
        # Update config
        self.bot.config["bot"]["prefix"] = new_prefix
        
        # Save to config.json
        try:
            config_path = os.path.join(self.bot.base_path, 'config', 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, indent=4, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ Prefix Updated",
                description=f"New prefix: `{new_prefix}`",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating prefix: {e}", ephemeral=True)

class SetDefaultModelView(discord.ui.View):
    def __init__(self, bot, user, models):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.add_item(SetDefaultModelSelect(bot, models))

class SetDefaultModelSelect(discord.ui.Select):
    def __init__(self, bot, models):
        self.bot = bot
        options = []
        for model_id, model_info in models.items():
            options.append(discord.SelectOption(
                label=model_info['display_name'],
                value=model_id,
                description=f"ID: {model_id}"
            ))
        
        super().__init__(
            placeholder="Select a model to set as default...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        model_id = self.values[0]
        model_info = self.bot.available_models.get(model_id)
        
        if not model_info:
            await interaction.response.send_message("❌ Model not found.", ephemeral=True)
            return
            
        # Update default model in config
        self.bot.config["settings"]["default_model"] = model_id
        
        # Save to config.json
        try:
            config_path = os.path.join(self.bot.base_path, 'config', 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.bot.config, f, indent=4, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ Default Model Set",
                description=f"New default model: **{model_info['display_name']}**",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting default model: {e}", ephemeral=True)

class ModelManagementView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
    
    @discord.ui.button(label="➕ Add Model", style=discord.ButtonStyle.success)
    async def add_model_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
            
        # Start the add model process
        cog = self.bot.get_cog("ModelManager")
        if cog:
            await cog.start_add_model_process(interaction)
        else:
            await interaction.response.send_message("❌ Model manager not available.", ephemeral=True)
    
    @discord.ui.button(label="🗑️ Remove Model", style=discord.ButtonStyle.danger)
    async def remove_model_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
            
        # Show model removal selection
        cog = self.bot.get_cog("ModelManager")
        if cog:
            await cog.show_remove_model_selection(interaction)
        else:
            await interaction.response.send_message("❌ Model manager not available.", ephemeral=True)

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}  # Simple cache for performance
        self.cache_timeout = 300  # 5 minutes
    
    def is_admin(self, user):
        """Check if user is admin"""
        return user.id in self.bot.config.get("bot", {}).get("admin_ids", [])
    
    def get_cached_data(self, key):
        """Get cached data if available and not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_timeout:
                return data
            else:
                # Remove expired cache
                del self.cache[key]
        return None
    
    def set_cached_data(self, key, data):
        """Set data in cache"""
        self.cache[key] = (data, datetime.now())
    
    @commands.hybrid_command(
        name="dashboard",
        description="Access the interactive bot dashboard"
    )
    async def dashboard(self, ctx: commands.Context):
        """واجهة مبسطة للوحة التحكم"""
        embed = discord.Embed(
            title="🤖 لوحة التحكم المبسطة",
            description="عرض سريع لحالة البوت وإحصائياته. الإعدادات وإدارة النماذج متاحة في لوحة الإدارة.",
            color=0x9b59b6
        )
        embed.add_field(name="📊 الحالة", value="اعرض حالة البوت الحالية", inline=False)
        embed.add_field(name="📈 الإحصائيات", value="إحصائيات واستخدام البوت", inline=False)
        
        view = DashboardView(self.bot, ctx.author)
        await ctx.send(embed=embed, view=view)

class ManageMenuSelect(discord.ui.Select):
    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        options = [
            discord.SelectOption(label="🧰 إدارة", value="manage", description="إدارة الإعدادات والنماذج والويبهوك"),
            discord.SelectOption(label="🔗 الويبهوك", value="webhooks", description="إضافة/حذف/اختبار الويبهوكات"),
            discord.SelectOption(label="⚙️ الإعدادات", value="settings", description="تعديل الإعدادات الأساسية"),
            discord.SelectOption(label="📋 النماذج", value="models", description="إدارة النماذج"),
        ]
        super().__init__(placeholder="اختر قسم الإدارة…", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ لا يمكنك استخدام هذه القائمة.", ephemeral=True)
            return
        choice = self.values[0]
        if choice in ("manage", "webhooks"):
            embed = discord.Embed(title="🔗 إدارة الويبهوك", description="أضف، احذف، اعرض، واختبر الويبهوكات.", color=0x00b894)
            view = WebhookManageView(self.bot, self.user)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        elif choice == "settings":
            embed = discord.Embed(title="⚙️ الإعدادات", description="تعديل الإعدادات الأساسية للبوت.", color=0xf1c40f)
            view = SettingsView(self.bot, self.user)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        elif choice == "models":
            embed = discord.Embed(title="📋 إدارة النماذج", description="إضافة/حذف/تبديل النماذج.", color=0x9b59b6)
            view = ModelManagementView(self.bot, self.user)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class AddWebhookModal(discord.ui.Modal, title="إضافة ويبهوك"):
    name = discord.ui.TextInput(label="الاسم", placeholder="مثال: errors", min_length=2, max_length=32)
    url = discord.ui.TextInput(label="الرابط", style=discord.TextStyle.short, placeholder="https://discord.com/api/webhooks/...", min_length=20)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            config_path = os.path.join(self.bot.base_path, 'config', 'webhooks.json')
            data = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
            data.setdefault('custom', {})
            data['custom'][str(self.name)] = str(self.url)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # تحديث كوج الويبهوك إن وجد
            logger_cog = self.bot.get_cog("WebhookLogger")
            if logger_cog and hasattr(logger_cog, 'custom_webhooks'):
                logger_cog.custom_webhooks[str(self.name)] = str(self.url)

            await interaction.response.send_message(f"✅ تمت إضافة الويبهوك `{self.name}`.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ أثناء الإضافة: {e}", ephemeral=True)

class DeleteWebhookModal(discord.ui.Modal, title="حذف ويبهوك"):
    name = discord.ui.TextInput(label="الاسم", placeholder="اسم الويبهوك للحذف", min_length=2, max_length=32)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            config_path = os.path.join(self.bot.base_path, 'config', 'webhooks.json')
            if not os.path.exists(config_path):
                await interaction.response.send_message("❌ لا يوجد ملف ويبهوكات.", ephemeral=True)
                return
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f) or {}
            custom = data.get('custom', {})
            if str(self.name) in custom:
                del custom[str(self.name)]
                data['custom'] = custom
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                # مزامنة مع الكوج
                logger_cog = self.bot.get_cog("WebhookLogger")
                if logger_cog and hasattr(logger_cog, 'custom_webhooks'):
                    logger_cog.custom_webhooks.pop(str(self.name), None)
                await interaction.response.send_message(f"🗑️ تم حذف `{self.name}`.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ هذا الاسم غير موجود.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ أثناء الحذف: {e}", ephemeral=True)

class TestWebhookModal(discord.ui.Modal, title="اختبار ويبهوك محدد"):
    target = discord.ui.TextInput(label="الاسم أو المعرف الجاهز", placeholder="مثال: errors أو default")

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        logger_cog = self.bot.get_cog("WebhookLogger")
        if not logger_cog:
            await interaction.response.send_message("❌ وحدة الويبهوك غير متاحة.", ephemeral=True)
            return
        try:
            embed = discord.Embed(title="Webhook Test", description=f"Testing `{self.target}`", color=0x00b894)
            embed.timestamp = discord.utils.utcnow()
            url = None
            if hasattr(logger_cog, 'custom_webhooks'):
                url = logger_cog.custom_webhooks.get(str(self.target))
            if not url:
                config_path = os.path.join(self.bot.base_path, 'config', 'webhooks.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f) or {}
                    url = data.get('custom', {}).get(str(self.target)) or data.get(str(self.target))
            if not url:
                await interaction.response.send_message("❌ لم يتم العثور على الويبهوك.", ephemeral=True)
                return
            if hasattr(logger_cog, '_send_to_url'):
                await logger_cog._send_to_url(url, embed)
            else:
                await interaction.response.send_message("❌ لا يمكن الإرسال؛ الدالة غير متاحة.", ephemeral=True)
                return
            await interaction.response.send_message("✅ تم إرسال رسالة اختبار.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ أثناء الاختبار: {e}", ephemeral=True)

class WebhookManageView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user

    @discord.ui.button(label="📜 عرض الويبهوكات", style=discord.ButtonStyle.secondary)
    async def list_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ لا يمكنك استخدام هذه القائمة.", ephemeral=True)
            return
        try:
            config_path = os.path.join(self.bot.base_path, 'config', 'webhooks.json')
            data = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
            custom = data.get('custom', {})
            embed = discord.Embed(title="📜 الويبهوكات المسجلة", color=0x2980b9)
            if custom:
                for name, url in custom.items():
                    display_url = url[:40] + "…" if len(url) > 40 else url
                    embed.add_field(name=name, value=display_url, inline=False)
            else:
                embed.description = "لا توجد ويبهوكات مخصصة بعد."
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ أثناء القراءة: {e}", ephemeral=True)

    @discord.ui.button(label="➕ إضافة", style=discord.ButtonStyle.success)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ لا يمكنك استخدام هذه القائمة.", ephemeral=True)
            return
        await interaction.response.send_modal(AddWebhookModal(self.bot))

    @discord.ui.button(label="🗑️ حذف", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ لا يمكنك استخدام هذه القائمة.", ephemeral=True)
            return
        await interaction.response.send_modal(DeleteWebhookModal(self.bot))

    @discord.ui.button(label="🧪 اختبار محدد", style=discord.ButtonStyle.primary)
    async def test_one_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ لا يمكنك استخدام هذه القائمة.", ephemeral=True)
            return
        await interaction.response.send_modal(TestWebhookModal(self.bot))

    @discord.ui.button(label="🧪 اختبار الكل", style=discord.ButtonStyle.secondary)
    async def test_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ لا يمكنك استخدام هذه القائمة.", ephemeral=True)
            return
        logger_cog = self.bot.get_cog("WebhookLogger")
        if not logger_cog:
            await interaction.response.send_message("❌ وحدة الويبهوك غير متاحة.", ephemeral=True)
            return
        try:
            config_path = os.path.join(self.bot.base_path, 'config', 'webhooks.json')
            data = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or {}
            urls = []
            if hasattr(logger_cog, 'custom_webhooks'):
                urls.extend(list(logger_cog.custom_webhooks.values()))
            urls.extend(list((data.get('custom', {}) or {}).values()))
            if not urls:
                await interaction.response.send_message("ℹ️ لا توجد ويبهوكات لإرسال الاختبار.", ephemeral=True)
                return
            for url in urls:
                embed = discord.Embed(title="Webhook Test", description="Bulk test", color=0x00b894)
                embed.timestamp = discord.utils.utcnow()
                if hasattr(logger_cog, '_send_to_url'):
                    await logger_cog._send_to_url(url, embed)
            await interaction.response.send_message("✅ تم إرسال اختبارات لجميع الويبهوكات.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ أثناء الاختبار: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Dashboard(bot))
