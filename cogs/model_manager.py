import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import os

# Modal for secure API key input
class APIKeyModal(discord.ui.Modal, title="Enter API Key Securely"):
    def __init__(self, cog, user_id, session):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.session = session
        
        # Add the API key input field (masked by default)
        self.api_key = discord.ui.TextInput(
            label="API Key",
            placeholder="Enter your OpenRouter API key here...",
            style=discord.TextStyle.short,
            required=False,
            max_length=100
        )
        self.add_item(self.api_key)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Store the API key in the session
        api_key = self.api_key.value if self.api_key.value else ""
        self.session['data']['api_key'] = api_key
        self.session['step'] = 4
        
        # Send confirmation to the user
        await interaction.response.send_message(
            "✅ API key received securely! Please return to the original channel to continue.",
            ephemeral=True
        )
        
        # Send the next step in the original channel
        channel = None
        if self.session.get('channel_id') is not None:
            channel = self.cog.bot.get_channel(self.session['channel_id'])
        else:
            channel = interaction.channel
            
        # Check if channel is a type that supports sending messages
        if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
            embed = discord.Embed(
                title="📝 Add New Model - Step 4/4",
                description="**Send a brief description of the model (optional)**\n\nIf you don't want to add a description, send `skip`",
                color=0x2ecc71
            )
            try:
                await channel.send(embed=embed)
            except Exception:
                # Channel doesn't support sending messages or other error occurred
                pass

# Create a view for the model management dashboard
class ModelManagementView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.bot = bot
        self.user = user
        self.base_path = bot.base_path
    
    @discord.ui.button(label="Add New Model", style=discord.ButtonStyle.success, custom_id="add_model")
    async def add_model_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
            
        # Start the add model process
        cog = self.bot.get_cog("ModelManager")
        if cog:
            await cog.start_add_model_process(interaction)
            # Disable all buttons after clicking one
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            if interaction.message is not None:
                await interaction.message.edit(view=self)
    
    @discord.ui.button(label="Remove Model", style=discord.ButtonStyle.danger, custom_id="remove_model")
    async def remove_model_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
            
        # Show model removal selection
        cog = self.bot.get_cog("ModelManager")
        if cog:
            await cog.show_remove_model_selection(interaction)
            # Disable all buttons after clicking one
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            if interaction.message is not None:
                await interaction.message.edit(view=self)
    
    @discord.ui.button(label="Set Default Model", style=discord.ButtonStyle.primary, custom_id="set_default")
    async def set_default_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
            
        # Show model selection for setting default
        cog = self.bot.get_cog("ModelManager")
        if cog:
            await cog.show_set_default_selection(interaction)
            # Disable all buttons after clicking one
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            if interaction.message is not None:
                await interaction.message.edit(view=self)
    
    @discord.ui.button(label="Switch Model", style=discord.ButtonStyle.secondary, custom_id="switch_model")
    async def switch_model_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return
            
        # Show model selection for switching
        cog = self.bot.get_cog("ModelManager")
        if cog:
            await cog.show_switch_model_selection(interaction)
            # Disable all buttons after clicking one
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            if interaction.message is not None:
                await interaction.message.edit(view=self)

# View for selecting a model to remove
class RemoveModelSelect(discord.ui.Select):
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
            placeholder="Select a model to remove...",
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
            
        # Check if it's a custom model
        if model_info.get("type") != "custom":
            await interaction.response.send_message("❌ Cannot remove default models. Only custom models can be removed.", ephemeral=True)
            return
            
        # Remove from database
        try:
            if not self.bot.db:
                await interaction.response.send_message("❌ Database not available.", ephemeral=True)
                return
                
            cursor = self.bot.db.cursor()
            cursor.execute("DELETE FROM custom_models WHERE model_id = ?", (model_id,))
            self.bot.db.commit()
            
            # Remove from available models
            del self.bot.available_models[model_id]
            
            # Save to models_config.json
            models_config_path = os.path.join(self.bot.base_path, 'config', 'models_config.json')
            with open(models_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.bot.available_models, f, indent=4, ensure_ascii=False)
            
            embed = discord.Embed(
                title="✅ Model Removed",
                description=f"Successfully removed model: **{model_info['display_name']}**",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log the model removal event
            webhook_logger = self.bot.get_cog("WebhookLogger")
            if webhook_logger:
                await webhook_logger.log_model_event(
                    "نموذج محذوف", 
                    interaction.user, 
                    model_info['display_name'],
                    "تم حذف النموذج بنجاح"
                )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing model: {e}", ephemeral=True)

class RemoveModelView(discord.ui.View):
    def __init__(self, bot, user, models):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.add_item(RemoveModelSelect(bot, models))

# View for selecting a model to set as default
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
            
            # Log the default model setting event
            webhook_logger = self.bot.get_cog("WebhookLogger")
            if webhook_logger:
                await webhook_logger.log_model_event(
                    "نموذج افتراضي محدد", 
                    interaction.user, 
                    model_info['display_name'],
                    "تم تعيين النموذج كافتراضي بنجاح"
                )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting default model: {e}", ephemeral=True)

class SetDefaultModelView(discord.ui.View):
    def __init__(self, bot, user, models):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.add_item(SetDefaultModelSelect(bot, models))

# View for selecting a model to switch to
class SwitchModelSelect(discord.ui.Select):
    def __init__(self, bot, models):
        self.bot = bot
        options = []
        for i, (model_id, model_info) in enumerate(models.items(), 1):
            options.append(discord.SelectOption(
                label=f"[{i}] {model_info['display_name']}",
                value=model_id,
                description=f"ID: {model_id}"
            ))
        
        super().__init__(
            placeholder="Select a model to switch to...",
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
            
            # Get numeric ID
            model_list = list(self.bot.available_models.items())
            numeric_id = None
            for index, (mid, _) in enumerate(model_list, 1):
                if mid == model_id:
                    numeric_id = str(index)
                    break
            
            embed = discord.Embed(
                title="✅ Model Switched",
                description=f"New default model: **{model_info['display_name']}** (ID: {numeric_id or model_id})",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log the model switching event
            webhook_logger = self.bot.get_cog("WebhookLogger")
            if webhook_logger:
                await webhook_logger.log_model_event(
                    "نموذج مبدل", 
                    interaction.user, 
                    model_info['display_name'],
                    f"تم تبديل النموذج بنجاح\nالمعرف: {numeric_id or model_id}"
                )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error switching model: {e}", ephemeral=True)

class SwitchModelView(discord.ui.View):
    def __init__(self, bot, user, models):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.add_item(SwitchModelSelect(bot, models))

class ModelManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_sessions = {}
        self.base_path = bot.base_path
    
    def is_admin(self, user):
        """Check if user is admin"""
        return user.id in self.bot.config.get("bot", {}).get("admin_ids", [])
    
    async def start_add_model_process(self, interaction: discord.Interaction):
        """Start the add model process"""
        # Start session
        if interaction.channel is not None:
            channel_id = interaction.channel.id
        else:
            channel_id = None
            
        self.setup_sessions[interaction.user.id] = {
            'step': 1,
            'data': {},
            'channel_id': channel_id
        }
        
        embed = discord.Embed(
            title="🆕 Add New Model - Step 1/4",
            description="**Send the model's display name as you want it to appear in the bot**\n\nExample: `DeepSeek Pro` or `My Custom AI`",
            color=0x3498db
        )
        embed.set_footer(text="Session will expire after 5 minutes of inactivity")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_remove_model_selection(self, interaction: discord.Interaction):
        """Show model removal selection"""
        if not self.bot.available_models:
            await interaction.response.send_message("❌ No models available to remove.", ephemeral=True)
            return
            
        # Filter custom models only
        custom_models = {k: v for k, v in self.bot.available_models.items() if v.get("type") == "custom"}
        
        if not custom_models:
            await interaction.response.send_message("❌ No custom models available to remove.", ephemeral=True)
            return
            
        view = RemoveModelView(self.bot, interaction.user, custom_models)
        embed = discord.Embed(
            title="🗑️ Remove Model",
            description="Select a custom model to remove:",
            color=0xe74c3c
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def show_set_default_selection(self, interaction: discord.Interaction):
        """Show set default model selection"""
        if not self.bot.available_models:
            await interaction.response.send_message("❌ No models available.", ephemeral=True)
            return
            
        view = SetDefaultModelView(self.bot, interaction.user, self.bot.available_models)
        embed = discord.Embed(
            title="⭐ Set Default Model",
            description="Select a model to set as default:",
            color=0xf1c40f
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def show_switch_model_selection(self, interaction: discord.Interaction):
        """Show switch model selection"""
        if not self.bot.available_models:
            await interaction.response.send_message("❌ No models available.", ephemeral=True)
            return
            
        view = SwitchModelView(self.bot, interaction.user, self.bot.available_models)
        embed = discord.Embed(
            title="🔄 Switch Model",
            description="Select a model to switch to:",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @commands.hybrid_command(
        name="admin_models",
        description="Access the comprehensive model management dashboard"
    )
    async def admin_models(self, ctx: commands.Context):
        """Display the comprehensive model management dashboard"""
        # Check permissions
        if not self.is_admin(ctx.author):
            await ctx.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🤖 Model Management Dashboard",
            description="Manage all aspects of AI models for the bot",
            color=0x9b59b6
        )
        
        # Display currently available models
        if self.bot.available_models:
            for model_id, model_info in self.bot.available_models.items():
                status = "🟢" if model_info.get('enabled', True) else "🔴"
                model_type = model_info.get('type', 'unknown').capitalize()
                usage_count = model_info.get('usage_count', 0)
                
                embed.add_field(
                    name=f"{status} {model_info['display_name']}",
                    value=f"🆔: `{model_id}`\n🏷️ Type: {model_type}\n📈 Usage: {usage_count}",
                    inline=False
                )
        else:
            embed.add_field(
                name="No Models Available",
                value="No models have been configured yet.",
                inline=False
            )
        
        view = ModelManagementView(self.bot, ctx.author)
        await ctx.send(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Process model addition messages"""
        if message.author.bot:
            return
        
        user_id = message.author.id
        if user_id not in self.setup_sessions:
            return
        
        session = self.setup_sessions[user_id]
        
        # Make sure message is in the same channel
        if session['channel_id'] is not None and message.channel.id != session['channel_id']:
            return
        
        try:
            await message.delete()
        except:
            pass
        
        if session['step'] == 1:
            await self.handle_model_name(message, session)
        elif session['step'] == 2:
            await self.handle_model_id(message, session)
        elif session['step'] == 3:
            await self.handle_api_key(message, session)
        elif session['step'] == 4:
            await self.handle_model_description(message, session)
    
    async def handle_model_name(self, message, session):
        """Handle model name input"""
        display_name = message.content.strip()
        
        # Validate display name
        if not display_name:
            channel = None
            if session.get('channel_id') is not None:
                channel = self.bot.get_channel(session['channel_id'])
            else:
                channel = message.channel
                
            if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                embed = discord.Embed(
                    title="❌ Invalid Display Name",
                    description="**Please provide a valid display name for the model**\n\n"
                               "The display name is how the model will appear in the bot's interface.\n\n"
                               "Examples:\n"
                               "- `GPT-4 Turbo`\n"
                               "- `Claude 3 Opus`\n"
                               "- `Gemini Pro`\n\n"
                               "Please try again with a valid display name.",
                    color=0xe74c3c
                )
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass
            return
            
        session['data']['display_name'] = display_name
        session['step'] = 2
        
        channel = None
        if session.get('channel_id') is not None:
            channel = self.bot.get_channel(session['channel_id'])
        else:
            channel = message.channel
            
        embed = discord.Embed(
            title="🆔 Add New Model - Step 2/4",
            description="**Send the Model ID for the model**\n\n"
                       "Model IDs should be in the format `provider/model-name`\n\n"
                       "Examples:\n"
                       "- `openai/gpt-4`\n"
                       "- `anthropic/claude-3-opus`\n"
                       "- `google/gemini-pro`\n\n"
                       "*For OpenRouter models, you can find the model ID on https://openrouter.ai/models*",
            color=0xf39c12
        )
        
        if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
            try:
                await channel.send(embed=embed)
            except Exception:
                # Channel doesn't support sending messages or other error occurred
                pass
    
    async def handle_model_id(self, message, session):
        """Handle Model ID input"""
        model_id = message.content.strip()
        
        # Validate model ID format for OpenRouter (should contain provider/model)
        if not model_id or ':' not in model_id:
            channel = None
            if session.get('channel_id') is not None:
                channel = self.bot.get_channel(session['channel_id'])
            else:
                channel = message.channel
                
            if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                embed = discord.Embed(
                    title="❌ Invalid Model ID",
                    description="**Please provide a valid OpenRouter model ID**\n\n"
                               "Model IDs should be in the format `provider/model-name`\n\n"
                               "Examples:\n"
                               "- `openai/gpt-4`\n"
                               "- `anthropic/claude-3-opus`\n"
                               "- `google/gemini-pro`\n\n"
                               "Please try again with a valid model ID.",
                    color=0xe74c3c
                )
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass
            return
        
        session['data']['model_id'] = model_id
        session['step'] = 3
        
        # Instead of sending a message in the channel, send a private message with a modal
        user = message.author
        try:
            embed = discord.Embed(
                title="🔑 Add New Model - Step 3/4",
                description="**Please click the button below to enter your API key securely**\n\n"
                           "Your API key will be masked and sent through a private message to protect it from being visible in chat history.\n\n"
                           "*Note: For OpenRouter, you can get an API key at https://openrouter.ai/keys*",
                color=0xe74c3c
            )
            
            # Create a view with a button to open the modal
            class APIKeyView(discord.ui.View):
                def __init__(self, cog, user_id, session):
                    super().__init__(timeout=120)
                    self.cog = cog
                    self.user_id = user_id
                    self.session = session
                
                @discord.ui.button(label="Enter API Key Securely", style=discord.ButtonStyle.primary)
                async def api_key_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != self.user_id:
                        await interaction.response.send_message("❌ You cannot use this button.", ephemeral=True)
                        return
                    
                    # Send the modal to the user
                    modal = APIKeyModal(self.cog, self.user_id, self.session)
                    await interaction.response.send_modal(modal)
            
            view = APIKeyView(self, user.id, session)
            
            channel = None
            if session.get('channel_id') is not None:
                channel = self.bot.get_channel(session['channel_id'])
            else:
                channel = message.channel
                
            if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                try:
                    await channel.send(embed=embed, view=view)
                except Exception:
                    # Channel doesn't support sending messages or other error occurred
                    pass
        except Exception as e:
            # Fallback to the original method if DM fails
            channel = None
            if session.get('channel_id') is not None:
                channel = self.bot.get_channel(session['channel_id'])
            else:
                channel = message.channel
                
            embed = discord.Embed(
                title="🔑 Add New Model - Step 3/4",
                description="**Send the API key for the model**\n\n"
                           "If you don't want to enter an API key now, send `skip`\n\n"
                           "*Note: For security, please delete your message after sending the API key*\n"
                           "*For OpenRouter, you can get an API key at https://openrouter.ai/keys*",
                color=0xe74c3c
            )
            
            if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                try:
                    await channel.send(embed=embed)
                except Exception:
                    # Channel doesn't support sending messages or other error occurred
                    pass
    
    async def handle_api_key(self, message, session):
        """Handle API key input (fallback method)"""
        # This is now a fallback method in case the modal doesn't work
        api_key = message.content.strip() if message.content.strip() != "skip" else ""
        session['data']['api_key'] = api_key
        session['step'] = 4
        
        channel = None
        if session.get('channel_id') is not None:
            channel = self.bot.get_channel(session['channel_id'])
        else:
            channel = message.channel
            
        embed = discord.Embed(
            title="📝 Add New Model - Step 4/4",
            description="**Send a brief description of the model (optional)**\n\n"
                       "This description will help users understand what the model is best for.\n\n"
                       "Examples:\n"
                       "- `Best for creative writing and storytelling`\n"
                       "- `Excellent at logical reasoning and math`\n"
                       "- `Multilingual support for 100+ languages`\n\n"
                       "If you don't want to add a description, send `skip`",
            color=0x2ecc71
        )
        
        if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
            try:
                await channel.send(embed=embed)
            except Exception:
                # Channel doesn't support sending messages or other error occurred
                pass
    
    async def handle_model_description(self, message, session):
        """Handle model description input"""
        description = message.content.strip() if message.content.strip() != "skip" else ""
        session['data']['description'] = description
        
        # Complete the model addition process
        await self.complete_model_addition(message, session)
    
    async def complete_model_addition(self, message, session):
        """Complete the model addition process with enhanced functionality"""
        channel = None
        try:
            # Get the channel for sending messages
            if session.get('channel_id') is not None:
                channel = self.bot.get_channel(session['channel_id'])
            else:
                channel = message.channel
                
            # Validate required data
            if 'display_name' not in session['data'] or 'model_id' not in session['data']:
                if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                    try:
                        await channel.send("❌ Missing required model information. Please restart the model addition process.")
                    except Exception:
                        pass
                return
                
            # Save to database
            if not self.bot.db:
                if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                    try:
                        await channel.send("❌ Database not available.")
                    except Exception:
                        pass
                return
                
            cursor = self.bot.db.cursor()
            # Use INSERT OR REPLACE to avoid conflicts
            cursor.execute('''
                INSERT OR REPLACE INTO custom_models (display_name, model_id, api_key, added_by)
                VALUES (?, ?, ?, ?)
            ''', (
                session['data']['display_name'],
                session['data']['model_id'], 
                session['data'].get('api_key', ''),
                str(message.author.id)
            ))
            self.bot.db.commit()
            
            # Update available models with proper structure
            new_model_data = {
                'display_name': session['data']['display_name'],
                'type': 'custom',  # Set type to 'custom' as requested
                'api_key': session['data'].get('api_key', ''),  # Use get() with default empty string
                'usage_count': 0,
                'enabled': True,
                'description': session['data'].get('description', '')  # Use get() with default empty string
            }
            
            # Update the bot's available models dictionary
            self.bot.available_models[session['data']['model_id']] = new_model_data
            
            # Save to models_config.json with proper structure
            models_config_path = os.path.join(self.bot.base_path, 'config', 'models_config.json')
            try:
                with open(models_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.bot.available_models, f, indent=4, ensure_ascii=False)
            except Exception as e:
                if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                    try:
                        await channel.send(f"❌ Error saving to models_config.json: {str(e)}")
                    except Exception:
                        pass
                return
            
            # Send success confirmation
            embed = discord.Embed(
                title="✅ Model Added Successfully!",
                description=f"**{session['data']['display_name']}**\nHas been successfully added to the bot 🎉",
                color=0x00ff00
            )
            embed.add_field(name="Model ID", value=f"`{session['data']['model_id']}`", inline=False)
            if session['data'].get('api_key'):
                embed.add_field(name="API Key", value="`••••••••`", inline=False)
            else:
                embed.add_field(name="API Key", value="`Not set`", inline=False)
            if session['data'].get('description'):
                embed.add_field(name="Description", value=session['data']['description'], inline=False)
            embed.set_footer(text="Model list automatically updated")
            
            # Log the model addition event
            webhook_logger = self.bot.get_cog("WebhookLogger")
            if webhook_logger:
                await webhook_logger.log_model_event(
                    "نموذج مضاف", 
                    message.author, 
                    session['data']['display_name'],
                    f"تم إضافة نموذج جديد بنجاح\nالمعرف: {session['data']['model_id']}"
                )
            
            if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                try:
                    await channel.send(embed=embed)
                except Exception:
                    # Channel doesn't support sending messages or other error occurred
                    pass
            
        except Exception as e:
            # Handle any errors during the model addition process
            error_channel = channel
            if error_channel is None and session.get('channel_id') is not None:
                error_channel = self.bot.get_channel(session['channel_id'])
            if error_channel is None:
                error_channel = message.channel
                
            embed = discord.Embed(
                title="❌ Model Addition Failed",
                description=f"An error occurred while adding the model: {str(e)}",
                color=0xff0000
            )
            if error_channel and isinstance(error_channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel, discord.Thread)):
                try:
                    await error_channel.send(embed=embed)
                except Exception:
                    pass
        finally:
            # Clean up session regardless of success or failure
            user_id = message.author.id
            if user_id in self.setup_sessions:
                del self.setup_sessions[user_id]

async def setup(bot):
    await bot.add_cog(ModelManager(bot))