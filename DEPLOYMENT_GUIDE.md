# AI Discord Bot - Railway.com Deployment Guide

## Project Overview

This is an advanced AI-powered Discord bot with the following core features:
- **AI Chat**: Powered by OpenRouter API with support for multiple models
- **Hybrid Commands**: Supports both slash commands and prefix-based commands
- **Code Generation**: Automatically detects and extracts code from AI responses
- **Statistics**: Comprehensive analytics with chart generation using matplotlib
- **Admin Panel**: Full administrative controls via `/admin` and `/dashboard`
- **Model Management**: Dynamic model switching and configuration
- **Multi-server Support**: Dedicated statistics for owner server and per-server basic stats
- **Direct Message Support**: Private conversations with the bot
- **Easy Setup**: Guided setup process via `/setup` command

## Project Contents

The project contains the following important files and folders:

### Core Files
- `main.py` - Main bot entry point
- `requirements.txt` - Python dependencies
- `README.md` - Project overview
- `SETUP_GUIDE.md` - Detailed setup instructions

### Directories
- `cogs/` - Functional modules (ai_chat.py, admin_panel.py, hybrid_commands.py, etc.)
- `config/` - Configuration files (config.json, models_config.json, webhooks.json)
- `database/` - Database manager and SQLite database file
- `templates/` - Discord message formatting templates
- `utils/` - Utility scripts for error handling, logging, localization, etc.

## Running the Bot Locally

### Prerequisites
1. Python 3.8 or higher
2. Discord bot token
3. OpenRouter API key

### Installation Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the bot:**
   - Edit `config/config.json` to add your Discord bot token and admin user IDs
   - Add your OpenRouter API keys in `config/models_config.json`

3. **Run the bot:**
   ```bash
   python main.py
   ```

## Deploying to Railway.com

### Method 1: Deploy from GitHub (Recommended)

1. **Fork this repository** to your GitHub account
2. **Login to Railway.com** and create a new project
3. **Connect your GitHub account** to Railway
4. **Select your forked repository** for deployment
5. **Configure environment variables** (see below)
6. **Deploy the application**

### Method 2: Deploy using Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Initialize a new Railway project:**
   ```bash
   railway init
   ```

4. **Deploy the project:**
   ```bash
   railway up
   ```

## Environment Variables

Railway.com uses environment variables for configuration. You need to set the following variables in your Railway project:

### Required Variables
- `DISCORD_TOKEN` - Your Discord bot token
- `OPENROUTER_API_KEY` - Your OpenRouter API key

### Optional Variables
- `BOT_PREFIX` - Custom bot prefix (default: "!")
- `OWNER_ID` - Discord user ID of the bot owner
- `LOG_LEVEL` - Logging level (default: "INFO")

### Setting Environment Variables on Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to the "Variables" tab
4. Add the required environment variables

Example configuration:
```
DISCORD_TOKEN=your_discord_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
BOT_PREFIX=!
OWNER_ID=123456789012345678
```

## Configuration Files

The bot uses JSON configuration files located in the `config/` directory:

### config.json
Main bot configuration including:
- Bot name and version
- Command prefix
- Admin user IDs
- Default settings

### models_config.json
AI model configuration including:
- Model IDs and display names
- API keys for each model
- Model-specific settings

### webhooks.json
Webhook URLs for logging and notifications

## Database

The bot uses SQLite for data persistence. The database file (`models.sqlite`) is automatically created in the `database/` directory on first run.

## Troubleshooting

### Common Issues

1. **Bot not responding to commands:**
   - Check that the bot has proper permissions in your Discord server
   - Verify that the bot token is correct
   - Ensure the bot is online

2. **AI responses not working:**
   - Check that your OpenRouter API key is valid
   - Verify that the model IDs in `models_config.json` are correct

3. **Deployment errors on Railway:**
   - Check that all environment variables are set correctly
   - Verify that the `requirements.txt` file includes all necessary dependencies

### Getting Help

If you encounter issues:
1. Check the bot logs for error messages
2. Refer to the `README.md` and `SETUP_GUIDE.md` files
3. Contact the development team for support

## Support

For additional support or feature requests, please open an issue on the GitHub repository or contact the development team.