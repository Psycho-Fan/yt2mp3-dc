# YouTube to MP3 Discord Bot

A private Discord bot that downloads audio from YouTube links as mp3, m4a, or webm files and sends them directly in your Discord server or DM. Only the authorized user can use the bot.

## Features
- **Download YouTube audio**: Supports mp3, m4a, and webm formats (no ffmpeg required)
- **Slash command and message support**: Use `/mp3` or just paste a YouTube link
- **File size check**: Ensures files are under Discord's 8MB upload limit
- **Age-restricted/Private videos**: Supports cookies.txt for authenticated downloads
- **Bot message cleanup**: `/clear` command deletes all bot messages in a channel
- **Security**: Only the specified user ID can use the bot

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/yt2mp3-discord-bot.git
cd yt2mp3-discord-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create a Discord bot and get your token
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application and bot
- Enable the `MESSAGE CONTENT INTENT` in the bot settings
- Copy the bot token

### 4. Set up your `.env` file
Create a `.env` file in the project root:
```
DISCORD_TOKEN=your-bot-token-here
```

### 5. (Optional) Add `cookies.txt` for age-restricted/private videos
- See `/cookies` command in Discord for instructions
- Place a valid `cookies.txt` (Netscape format) in the project root

### 6. Set your Discord user ID
Edit `yt2mp3_discord_bot.py` and set `AUTHORIZED_USER_ID` to your Discord user ID (as an integer).

## Usage

- **/mp3 <YouTube URL>**: Download audio from a YouTube link
- **Paste a YouTube link**: The bot will automatically reply with the audio file
- **/clear**: Delete all bot messages in the current channel
- **/cookies**: Get instructions for generating a valid `cookies.txt`

## Notes
- The bot only responds to the authorized user ID for all commands and messages
- Maximum file size is 8MB (Discord's default limit)
- No ffmpeg required; downloads in the best available audio format

## Deploy
Run the bot with:
```bash
python yt2mp3_discord_bot.py
```

## License
MIT 