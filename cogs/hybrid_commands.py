import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import re
import os
import tempfile
import io
from datetime import datetime, timedelta
from AI_Discord_Bot.utils.branding import apply_branding, BRAND

# Try to import matplotlib for chart generation
# Using try/except to handle cases where matplotlib is not installed
MATPLOTLIB_AVAILABLE = False
matplotlib_module = None
pyplot_module = None

try:
    matplotlib_module = __import__('matplotlib')
    matplotlib_module.use('Agg')  # Use non-interactive backend
    pyplot_module = __import__('matplotlib.pyplot', fromlist=[''])
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Warning: matplotlib not available. Charts will not be generated.")

class HybridCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name='تحليل الرسالة',
            callback=self.analyze_message,
        )
        self.bot.tree.add_command(self.ctx_menu)
    
    # أمر هجين: يعمل بكلتا الطريقتين
    @commands.hybrid_command(
        name="chat",
        description="محادثة مع الذكاء الاصطناعي"
    )
    @app_commands.describe(message="الرسالة التي تريد إرسالها")
    async def chat(self, ctx: commands.Context, *, message: str):
        """أمر محادثة يعمل بالبريفكس والسلاش"""
        
        # إظهار أن البوت يعمل على الرد
        await ctx.defer()
        
        try:
            # استخدام النموذج الافتراضي
            response = await self.generate_ai_response(message, ctx.author.id)
            
            # التأكد من أن الرد ليس فارغًا
            if not response or response.strip() == "":
                response = "I'm sorry, I couldn't generate a proper response. Please try rephrasing your question."
            
            # Check if this is a programming request and extract code
            if self.is_programming_request(message):
                code_blocks = self.extract_code_from_response(response)
                if code_blocks:
                    # Create files and send them
                    files = []
                    for language, code in code_blocks:
                        file_extension = self.get_file_extension(language)
                        file_name = f"code_{ctx.author.id}_{len(files)+1}{file_extension}"
                        
                        # Create a temporary file
                        temp_file_path = os.path.join(tempfile.gettempdir(), file_name)
                        try:
                            with open(temp_file_path, 'w', encoding='utf-8') as f:
                                f.write(code)
                            
                            # Create a discord file object
                            discord_file = discord.File(temp_file_path, filename=file_name)
                            files.append(discord_file)
                            
                            # Log successful code generation
                            await self.log_code_generation(ctx.author.id, message, response, language, True)
                        except Exception as e:
                            # Log failed code generation
                            await self.log_code_generation(ctx.author.id, message, response, language, False, str(e))
                            print(f"Error creating file: {e}")
                    
                    # Send the response with files
                    embed = discord.Embed(
                        description=response,
                        color=0x3498db
                    )
                    embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
                    embed.set_footer(text="Powered by Open Router AI")
                    
                    await ctx.send(embed=embed, files=files)
                    
                    # Clean up temporary files
                    for file in files:
                        try:
                            os.remove(file.fp.name)
                        except:
                            pass
                    
                    return
            
            # إرسال الرد العادي إذا لم يكن هناك كود
            embed = discord.Embed(
                description=response,
                color=0x3498db
            )
            embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            embed.set_footer(text="Powered by Open Router AI")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ: {str(e)}")

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
        code_blocks = re.findall(r'``(\w*)\n(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            return code_blocks
        
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
        # This will be implemented in the AIChat cog
        ai_chat_cog = self.bot.get_cog("AIChat")
        if ai_chat_cog and hasattr(ai_chat_cog, 'log_code_generation'):
            await ai_chat_cog.log_code_generation(user_id, message, response, language, success, error)

    async def generate_ai_response(self, message, user_id):
        """توليد رد من الذكاء الاصطناعي باستخدام OpenRouter"""
        # هذه الدالة تستخدم الـ cog الخاص بالدردشة
        ai_chat_cog = self.bot.get_cog("AIChat")
        if ai_chat_cog:
            # الحصول على النموذج الافتراضي من الإعدادات
            default_model = self.bot.config.get("settings", {}).get("default_model", "tngtech/deepseek-r1t2-chimera:free")
            return await ai_chat_cog.generate_response(message, user_id, default_model)
        else:
            return "عذراً، نظام الدردشة غير متاح حالياً."
    
    @commands.hybrid_command(
        name="models",
        description="عرض النماذج المتاحة والتبديل بينها"
    )
    async def models(self, ctx: commands.Context):
        """عرض قائمة النماذج بشكل تفاعلي"""
        # Import the SwitchModelView from model_manager
        try:
            from cogs.model_manager import SwitchModelView
        except ImportError:
            await ctx.send("❌ Model manager not available.")
            return
        
        embed = discord.Embed(
            title="🤖 Available AI Models",
            description="Choose a model to use:",
            color=0x9b59b6
        )
        
        # إنشاء مخطط ترقيق بسيط للنماذج
        model_list = list(self.bot.available_models.items())
        
        # إضافة النماذج المتاحة مع IDs الرقمية فقط
        for index, (model_id, model_info) in enumerate(model_list, 1):
            status = "🟢" if model_info.get('enabled', True) else "🔴"
            embed.add_field(
                name=f"{status} [{index}] {model_info['display_name']}",
                value=f"ID: {index}",
                inline=False
            )
        
        # إنشاء العرض التفاعلي مع الأزرار
        view = SwitchModelView(self.bot, ctx.author, self.bot.available_models)
        embed.set_footer(text="Select a model from the dropdown to switch")
        await ctx.send(embed=embed, view=view)
    
    @commands.hybrid_command(
        name="stats",
        description="عرض إحصائيات البوت"
    )
    async def stats(self, ctx: commands.Context):
        """عرض إحصائيات متقدمة"""
        
        # Check if this is the owner server
        is_owner_server = self.is_owner_server(ctx.guild)
        
        if is_owner_server:
            # Show comprehensive stats for owner
            await self.show_owner_stats(ctx)
        else:
            # Show usage stats for subsidiary servers
            await self.show_subscriber_stats(ctx)
    
    def is_owner_server(self, guild):
        """Check if the current server is the owner server"""
        if not guild:
            return False
        # Check if the guild ID matches the owner server ID in config
        owner_server_id = self.bot.config.get("bot", {}).get("owner_server_id")
        return owner_server_id and guild.id == owner_server_id
    
    async def show_owner_stats(self, ctx):
        """Show comprehensive statistics for the owner"""
        # جمع البيانات
        total_users = len(self.bot.users)
        total_servers = len(self.bot.guilds)
        uptime = discord.utils.utcnow() - self.bot.start_time
        
        # Get database stats
        total_conversations = 0
        total_code_generations = 0
        successful_code_generations = 0
        
        if self.bot.db:
            try:
                cursor = self.bot.db.cursor()
                
                # Total conversations
                cursor.execute("SELECT COUNT(*) FROM conversation_logs")
                result = cursor.fetchone()
                total_conversations = result[0] if result else 0
                
                # Total code generations
                cursor.execute("SELECT COUNT(*) FROM code_generation_logs")
                result = cursor.fetchone()
                total_code_generations = result[0] if result else 0
                
                # Successful code generations
                cursor.execute("SELECT COUNT(*) FROM code_generation_logs WHERE success = 1")
                result = cursor.fetchone()
                successful_code_generations = result[0] if result else 0
            except Exception as e:
                print(f"Error fetching database stats: {e}")
        
        embed = discord.Embed(
            title="📊 إحصائيات البوت - لوحة التحكم الكاملة",
            color=0xf1c40f
        )
        
        embed.add_field(name="👥 المستخدمون", value=total_users, inline=True)
        embed.add_field(name="🖥️ السيرفرات", value=total_servers, inline=True)
        embed.add_field(name="⏰ وقت التشغيل", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="🤖 النماذج", value=len(self.bot.available_models), inline=True)
        embed.add_field(name="⚡ البينج", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="💾 الإصدار", value="v2.0.0", inline=True)
        embed.add_field(name="💬 إجمالي المحادثات", value=total_conversations, inline=True)
        embed.add_field(name="💻 إجمالي توليد الكود", value=total_code_generations, inline=True)
        embed.add_field(name="✅ توليد الكود الناجح", value=successful_code_generations, inline=True)
        
        # Success rate
        if total_code_generations > 0:
            success_rate = (successful_code_generations / total_code_generations) * 100
            embed.add_field(name="📈 معدل النجاح", value=f"{success_rate:.1f}%", inline=True)
        
        # Generate charts if matplotlib is available
        if MATPLOTLIB_AVAILABLE:
            try:
                chart_file = await self.generate_usage_chart()
                if chart_file:
                    embed.set_image(url="attachment://usage_chart.png")
                    await ctx.send(embed=embed, file=chart_file)
                    return
            except Exception as e:
                print(f"Error generating chart: {e}")
        
        await ctx.send(embed=embed)
    
    async def show_subscriber_stats(self, ctx):
        """Show usage statistics for subsidiary servers"""
        # جمع البيانات
        total_users = len(self.bot.users)
        total_servers = len(self.bot.guilds)
        uptime = discord.utils.utcnow() - self.bot.start_time
        
        embed = discord.Embed(
            title="📊 إحصائيات البوت - الإحصائيات العامة",
            color=0xf1c40f
        )
        
        embed.add_field(name="👥 المستخدمون", value=total_users, inline=True)
        embed.add_field(name="🖥️ السيرفرات", value=total_servers, inline=True)
        embed.add_field(name="⏰ وقت التشغيل", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="🤖 النماذج", value=len(self.bot.available_models), inline=True)
        embed.add_field(name="⚡ البينج", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="💾 الإصدار", value="v2.0.0", inline=True)
        
        await ctx.send(embed=embed)
    
    async def generate_usage_chart(self):
        """Generate a usage chart for the last 7 days"""
        if not MATPLOTLIB_AVAILABLE or not self.bot.db:
            return None
            
        # Only proceed if matplotlib was successfully imported
        if pyplot_module is None:
            return None
            
        try:
            cursor = self.bot.db.cursor()
            
            # Get daily usage data for the last 7 days
            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM conversation_logs 
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Extract data
            dates = [row[0] for row in rows]
            counts = [row[1] for row in rows]
            
            # Create the chart
            fig, ax = pyplot_module.subplots(figsize=(10, 6))
            ax.plot(dates, counts, marker='o', linewidth=2, markersize=8, color='#3498db')
            ax.set_title('Bot Usage Over Time (Last 7 Days)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Number of Interactions', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
            pyplot_module.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            pyplot_module.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            pyplot_module.close(fig)
            
            return discord.File(buf, filename="usage_chart.png")
        except Exception as e:
            print(f"Error creating usage chart: {e}")
            return None
    
    @commands.hybrid_command(
        name="setup",
        description="Setup the bot for your server"
    )
    async def setup_command(self, ctx: commands.Context):
        """Setup command for easy deployment"""
        # Check if user has administrator permissions
        if not isinstance(ctx.author, discord.Member) or not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        # Ask if they want to restrict bot to a specific channel
        embed = discord.Embed(
            title="🤖 Bot Setup Guide",
            description="Follow these steps to set up the bot in your server:",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="1. Configure Admins",
            value="Add your user ID to the admin list in `config/config.json` under `admin_ids`",
            inline=False
        )
        
        embed.add_field(
            name="2. Set Default Model",
            value="Use `/models` to view available models and set a default",
            inline=False
        )
        
        embed.add_field(
            name="3. Configure Dedicated Channel (Optional)",
            value="Use `/admin set_dedicated_channel` to set up a dedicated chat channel",
            inline=False
        )
        
        embed.add_field(
            name="4. Customize Prefix",
            value="Use `/dashboard` then click Settings to change the bot prefix",
            inline=False
        )
        
        embed.add_field(
            name="5. Add Custom Models",
            value="Use `/admin_models` to add your own OpenRouter models",
            inline=False
        )
        
        embed.add_field(
            name="6. Restrict to Specific Channel (Recommended)",
            value="Would you like to restrict the bot to only respond in a specific channel? Reply with 'yes' or 'no'.",
            inline=False
        )
        
        embed.add_field(
            name="Need Help?",
            value="Visit our support server or check the documentation for more information",
            inline=False
        )
        
        setup_message = await ctx.send(embed=embed)
        
        # Wait for response about channel restriction
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            if msg.content.lower() in ['yes', 'y', 'نعم']:
                # Ask for channel
                await ctx.send("Please mention the channel you want the bot to respond in (e.g., #general):")
                
                channel_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                
                # Extract channel ID from mention
                if channel_msg.channel_mentions:
                    channel_id = channel_msg.channel_mentions[0].id
                    # Update config
                    self.bot.config["settings"]["dedicated_channel_id"] = channel_id
                    self.bot.save_config()
                    await ctx.send(f"✅ Bot will now only respond in <#{channel_id}>")
                else:
                    await ctx.send("❌ Invalid channel mention. Please use #channel-name format.")
        except asyncio.TimeoutError:
            await ctx.send("Setup process timed out. You can continue setup later.")
        
        await ctx.send("✅ Setup process completed! The bot is now configured.")
    
    @commands.hybrid_command(
        name="help",
        description="عرض جميع الأوامر المتاحة"
    )
    async def help_command(self, ctx: commands.Context):
        """عرض مساعدة متقدمة"""
        
        embed = discord.Embed(
            title="📖 مركز المساعدة - الأوامر الهجينة",
            description="يمكنك استخدام هذه الأوامر إما بالبريفكس أو بأوامر السلاش",
            color=0x2ecc71
        )
        
        # أوامر الدردشة
        embed.add_field(
            name="🤖 أوامر الدردشة",
            value=(
                "`/chat` - محادثة مع الذكاء الاصطناعي\n"
                "`/models` - عرض النماذج المتاحة وتبديل بينها\n"
                "`/code_stats` - عرض إحصائيات توليد الكود\n"
                "`/admin_models` - لوحة إدارة النماذج (للمسؤولين فقط)"
            ),
            inline=False
        )
        
        # أوامر المعلومات
        embed.add_field(
            name="ℹ️ أوامر المعلومات",
            value=(
                "`/stats` - عرض إحصائيات البوت\n"
                "`/help` - عرض هذه المساعدة\n"
                "`/about` - معلومات عن البوت"
            ),
            inline=False
        )
        
        # أوامر الإدارة
        embed.add_field(
            name="⚙️ أوامر الإدارة",
            value=(
                "`/admin` - لوحة تحكم المشرف\n"
                "`/add_model` - إضافة نموذج جديد\n"
                "`/remove_model` - إزالة نموذج"
            ),
            inline=False
        )
        
        # أوامر الإعداد
        embed.add_field(
            name="🛠️ أوامر الإعداد",
            value=(
                "`/setup` - إعداد البوت لسيرفرك\n"
                "`/dashboard` - لوحة التحكم التفاعلية"
            ),
            inline=False
        )
        
        embed.set_footer(text="يمكنك استخدام البريفكس ! أو / قبل أي أمر")
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="about",
        description="معلومات عن البوت"
    )
    async def about(self, ctx: commands.Context):
        """عرض معلومات عن البوت"""
        
        embed = discord.Embed(
            title="🤖 عن البوت",
            description=f"{BRAND['bot_name']} • {BRAND['powered_by']}",
            color=0xe74c3c
        )
        embed.add_field(
            name="👨‍💻 المطور",
            value=f"{BRAND['developer']} (Discord: {BRAND['developer_discord']})",
            inline=False
        )
        embed.add_field(
            name="📋 المميزات",
            value=(
                "• أوامر هجينة (سلاش + بريفكس)\n"
                "• تكامل مع OpenRouter API\n"
                "• نماذج مخصصة ودعم متعدد اللغات\n"
                "• لوحة تحكم مبسطة وإحصائيات\n"
                "• تسجيل عبر ويبهوك مع قيود أمان"
            ),
            inline=False
        )
        embed.add_field(
            name="🔗 روابط",
            value=(
                "[OpenRouter](https://openrouter.ai/)\n"
                "[discord.py](https://discordpy.readthedocs.io/)"
            ),
            inline=False
        )
        embed = apply_branding(embed)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="code_stats",
        description="عرض إحصائيات توليد الكود"
    )
    async def code_stats(self, ctx: commands.Context):
        """عرض إحصائيات توليد الكود"""
        # This will be implemented by getting stats from the database
        if not self.bot.db:
            await ctx.send("❌ قاعدة البيانات غير متاحة.")
            return
            
        try:
            cursor = self.bot.db.cursor()
            # Get overall code generation stats
            cursor.execute('''
                SELECT language, COUNT(*) as count, AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate
                FROM code_generation_logs 
                GROUP BY language
                ORDER BY count DESC
            ''')
            rows = cursor.fetchall()
            
            if not rows:
                await ctx.send("❌ لم يتم توليد أي كود بعد.")
                return
            
            embed = discord.Embed(
                title="📊 إحصائيات توليد الكود",
                description="إحصائيات توليد الكود حسب اللغة:",
                color=0x9b59b6
            )
            
            total_generations = sum(row[1] for row in rows)  # count is at index 1
            embed.add_field(name="إجمالي عمليات التوليد", value=total_generations, inline=False)
            
            for row in rows:
                language, count, success_rate = row
                success_rate = success_rate * 100 if success_rate else 0
                embed.add_field(
                    name=f"{language}",
                    value=f"العدد: {count}\نمعدل النجاح: {success_rate:.1f}%",
                    inline=True
                )
            # Get user-specific stats
            cursor.execute('''
                SELECT COUNT(*) as user_count
                FROM code_generation_logs 
                WHERE user_id = ?
            ''', (str(ctx.author.id),))
            user_row = cursor.fetchone()
            
            if user_row:
                embed.add_field(name="توليداتك", value=user_row[0], inline=False)
            
            # Generate code stats chart if matplotlib is available
            if MATPLOTLIB_AVAILABLE:
                try:
                    chart_file = await self.generate_code_stats_chart()
                    if chart_file:
                        embed.set_image(url="attachment://code_stats_chart.png")
                        await ctx.send(embed=embed, file=chart_file)
                        return
                except Exception as e:
                    print(f"Error generating code stats chart: {e}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ حدث خطأ: {str(e)}")
    
    async def generate_code_stats_chart(self):
        """Generate a code stats chart"""
        if not MATPLOTLIB_AVAILABLE or not self.bot.db:
            return None
            
        # Only proceed if matplotlib was successfully imported
        if pyplot_module is None:
            return None
            
        try:
            cursor = self.bot.db.cursor()
            
            # Get code generation stats
            cursor.execute("""
                SELECT language, COUNT(*) as count
                FROM code_generation_logs 
                WHERE success = 1
                GROUP BY language
                ORDER BY count DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Extract data
            languages = [row[0] for row in rows]
            counts = [row[1] for row in rows]
            
            # Create the chart
            fig, ax = pyplot_module.subplots(figsize=(10, 8))
            colors = pyplot_module.cm.Set3(range(len(languages)))
            wedges, texts, autotexts = ax.pie(counts, labels=languages, autopct='%1.1f%%', 
                                              startangle=90, colors=colors)
            ax.set_title('Code Generation by Language', fontsize=16, fontweight='bold')
            ax.axis('equal')
            pyplot_module.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            pyplot_module.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            pyplot_module.close(fig)
            
            return discord.File(buf, filename="code_stats_chart.png")
        except Exception as e:
            print(f"Error creating code stats chart: {e}")
            return None

    async def analyze_message(self, interaction: discord.Interaction, message: discord.Message):
        """تحليل رسالة من قائمة السياق"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # استخدام النموذج الافتراضي لتحليل الرسالة
            prompt = f"قم بتحليل هذه الرسالة وتلخيص محتواها: {message.content}"
            response = await self.generate_ai_response(prompt, interaction.user.id)
            
            embed = discord.Embed(
                title="✨ تحليل الرسالة",
                description=response,
                color=0x1abc9c
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ حدث خطأ: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(HybridCommands(bot))
