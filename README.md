# AI Discord Bot

An advanced Discord bot powered by OpenRouter API that provides AI chat capabilities with multiple models, comprehensive statistics, and easy deployment.

## Features

- **Hybrid Command Support**: Works with both prefix and slash commands
- **Multiple AI Models**: Supports various AI models through OpenRouter
- **Code Generation**: Automatically detects and extracts code from AI responses
- **Comprehensive Statistics**: Detailed analytics with automatic chart generation
- **Model Management**: Add, remove, and switch between custom AI models
- **Admin Panel**: Full administrative controls for bot management
- **Dedicated Channels**: Set up channels for automatic AI chat
- **Direct Message Support**: Chat with the bot privately
- **Owner Server**: Dedicated comprehensive statistics for the bot owner
- **Easy Setup**: Simple deployment process with setup command

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure the bot:
   - Edit `config/config.json` to add your admin IDs and preferences
   - Edit `config/models_config.json` to configure AI models
   - Update the bot token in `main.py`

3. Run the bot:
   ```
   python main.py
   ```

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Commands

### Chat Commands
- `/chat <message>` - Chat with the AI
- `/models` - View and switch between available models

### Information Commands
- `/stats` - View bot statistics (comprehensive for owner server, basic for others)
- `/code_stats` - View code generation statistics
- `/help` - Show help information
- `/about` - Show information about the bot

### Admin Commands
- `/admin` - Access the admin panel
- `/admin_models` - Manage AI models
- `/dashboard` - Interactive bot dashboard

### Setup Commands
- `/setup` - Easy setup guide for your server

## Configuration

The bot can be configured through:
- `config/config.json` - General bot settings
- `config/models_config.json` - AI model configurations

## Requirements

- Python 3.8+
- Discord.py 2.3.0
- OpenRouter API key

## License

This project is licensed under the MIT License.