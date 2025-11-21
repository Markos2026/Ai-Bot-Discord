# AI Discord Bot - Setup Guide

## Prerequisites

1. Python 3.8 or higher
2. A Discord account and a bot token from the Discord Developer Portal
3. An OpenRouter API key (get one at https://openrouter.ai/keys)

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Edit `config/config.json`:
   - Add your Discord user ID to the `admin_ids` array
   - Set your preferred bot prefix
   - Add your owner server ID if you want to use the comprehensive stats feature

2. Edit `config/models_config.json`:
   - Add or modify AI models as needed
   - Update API keys for each model

3. In `main.py`, replace the placeholder token with your actual bot token:
   ```python
   token = "YOUR_BOT_TOKEN_HERE"
   ```

## Running the Bot

Execute the bot with:
```
python main.py
```

## Setting Up Your Server

1. Invite the bot to your server using the OAuth2 URL generated in the Discord Developer Portal
2. Use the `/setup` command in your server to get setup instructions
3. Configure admin users with the `/admin` commands
4. Set up a dedicated channel for automatic chat if desired

## Features

- **Hybrid Commands**: Use both prefix and slash commands
- **AI Chat**: Chat with multiple AI models through OpenRouter
- **Model Management**: Add, remove, and switch between AI models
- **Statistics**: View usage statistics with automatic chart generation
- **Code Generation**: Automatically detect and extract code from AI responses
- **Admin Panel**: Comprehensive admin controls for bot management

## Owner Server Features

If you set up an owner server:
- View comprehensive statistics with charts
- Monitor all bot usage across servers
- Access detailed analytics

For subsidiary servers:
- View basic usage statistics
- Access standard bot features

## Support

For issues or questions, please check the documentation or contact the development team.