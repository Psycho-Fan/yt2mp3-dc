import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import tempfile
import re

# Load token from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

# Only this user ID can use the bot
AUTHORIZED_USER_ID = 1187151195001851924

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="/", intents=intents)

# YouTube URL regex pattern
YOUTUBE_URL_PATTERN = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})'

def is_authorized_user(user_id):
    """Check if user is authorized to use the bot"""
    return user_id == AUTHORIZED_USER_ID

def validate_cookies_file(cookies_file):
    """Validate if cookies.txt is in correct Netscape format"""
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # Check for Netscape header
            has_header = False
            for line in lines:
                line = line.strip()
                if line.startswith('# Netscape HTTP Cookie File'):
                    has_header = True
                    break
            
            # Check for valid cookie lines (tab-separated with 7 fields)
            valid_cookies = 0
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    fields = line.split('\t')
                    if len(fields) >= 7:
                        valid_cookies += 1
            
            return has_header and valid_cookies > 0
            
    except Exception:
        return False

def download_audio(url, temp_dir):
    ydl_opts = {
        'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [],  # No postprocessing, no ffmpeg
    }
    
    # Add cookies.txt if it exists and is valid
    cookies_file = 'cookies.txt'
    if os.path.exists(cookies_file):
        if validate_cookies_file(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            print(f"Using cookies from: {cookies_file}")
        else:
            print(f"⚠️ {cookies_file} is not in correct Netscape format - skipping cookies")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise Exception("Failed to extract video info")
        
        ext = info.get('ext', 'm4a')
        title = info.get('title', 'audio')
        
        # Find the downloaded file
        downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith(ext)]
        if not downloaded_files:
            raise Exception("No audio file was downloaded")
        
        filepath = os.path.join(temp_dir, downloaded_files[0])
        return filepath, title

async def process_youtube_url(url, interaction_or_message):
    """Process YouTube URL and send audio file"""
    # Check authorization
    user_id = interaction_or_message.author.id if hasattr(interaction_or_message, 'author') else interaction_or_message.user.id
    
    if not is_authorized_user(user_id):
        error_msg = "❌ You are not authorized to use this bot."
        if hasattr(interaction_or_message, 'response'):
            await interaction_or_message.followup.send(error_msg, ephemeral=True)
        else:
            await interaction_or_message.reply(error_msg, ephemeral=True)
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            filepath, title = download_audio(url, temp_dir)
            
            # Check file size (Discord limit is 8MB for regular servers, 25MB for Nitro)
            file_size = os.path.getsize(filepath)
            if file_size > 8 * 1024 * 1024:  # 8MB limit
                error_msg = f"❌ File too large ({file_size/1024/1024:.1f}MB). Discord limit is 8MB."
                if hasattr(interaction_or_message, 'response'):
                    await interaction_or_message.followup.send(error_msg, ephemeral=True)
                else:
                    await interaction_or_message.reply(error_msg)
                return
            
            # Send the file
            if hasattr(interaction_or_message, 'response'):
                # Slash command interaction
                await interaction_or_message.followup.send(
                    content=f"**{title}**",
                    file=discord.File(filepath)
                )
            else:
                # Regular message
                await interaction_or_message.reply(
                    content=f"**{title}**",
                    file=discord.File(filepath)
                )
            
        except yt_dlp.utils.DownloadError as e:
            error_msg = f"❌ Download error: {str(e)}"
            if hasattr(interaction_or_message, 'response'):
                await interaction_or_message.followup.send(error_msg, ephemeral=True)
            else:
                await interaction_or_message.reply(error_msg)
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            if hasattr(interaction_or_message, 'response'):
                await interaction_or_message.followup.send(error_msg, ephemeral=True)
            else:
                await interaction_or_message.reply(error_msg)

@bot.tree.command(name="mp3", description="Download audio from a YouTube link as mp3/m4a/webm.")
@app_commands.describe(url="YouTube video URL")
async def mp3(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await process_youtube_url(url, interaction)

@bot.tree.command(name="clear", description="Delete all bot messages in this channel.")
async def clear(interaction: discord.Interaction):
    # Check authorization
    if not is_authorized_user(interaction.user.id):
        await interaction.response.send_message("❌ You are not authorized to use this bot.", ephemeral=True)
        return
    
    # Check if channel supports message history (text channels or DMs)
    if not isinstance(interaction.channel, (discord.TextChannel, discord.DMChannel)):
        await interaction.response.send_message("❌ This command only works in text channels and DMs.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        deleted_count = 0
        async for message in interaction.channel.history(limit=100):
            if message.author == bot.user:
                try:
                    await message.delete()
                    deleted_count += 1
                except discord.Forbidden:
                    # Skip messages we can't delete (e.g., old messages)
                    continue
        
        # Send result as a new message instead of followup
        if deleted_count > 0:
            await interaction.channel.send(f"🗑️ Deleted {deleted_count} bot messages.", delete_after=5)
        else:
            await interaction.channel.send("ℹ️ No bot messages found to delete.", delete_after=5)
            
    except Exception as e:
        try:
            await interaction.channel.send(f"❌ Error clearing messages: {str(e)}", delete_after=10)
        except:
            # If we can't send to channel, try to send as ephemeral followup
            try:
                await interaction.followup.send(f"❌ Error clearing messages: {str(e)}", ephemeral=True)
            except:
                pass  # If all else fails, just ignore the error

@bot.tree.command(name="cookies", description="Get instructions for generating correct cookies.txt format.")
async def cookies(interaction: discord.Interaction):
    # Check authorization
    if not is_authorized_user(interaction.user.id):
        await interaction.response.send_message("❌ You are not authorized to use this bot.", ephemeral=True)
        return
    
    instructions = """**How to generate correct cookies.txt:**

**Method 1: yt-dlp (Recommended)**
```bash
yt-dlp --cookies-from-browser chrome
```

**Method 2: Browser Extension**
1. Install "Get cookies.txt" extension
2. Go to YouTube and log in
3. Export cookies in Netscape format
4. Save as `cookies.txt`

**Method 3: Manual Format**
Your cookies.txt should look like:
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1735689600	VISITOR_INFO1_LIVE	abc123
.youtube.com	TRUE	/	FALSE	1735689600	LOGIN_INFO	abc123
```

**Current Status:** Your cookies.txt format is invalid."""
    
    await interaction.response.send_message(instructions, ephemeral=True)

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if message contains YouTube URL
    youtube_urls = re.findall(YOUTUBE_URL_PATTERN, message.content)
    
    if youtube_urls:
        # Convert video ID back to full URL
        video_id = youtube_urls[0]
        full_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Send typing indicator
        async with message.channel.typing():
            await process_youtube_url(full_url, message)
    
    # Process commands (important for slash commands to work)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Bot is restricted to user ID: {AUTHORIZED_USER_ID}')
    
    # Check for cookies.txt
    if os.path.exists('cookies.txt'):
        if validate_cookies_file('cookies.txt'):
            print("✅ cookies.txt found and valid - age-restricted videos supported")
        else:
            print("⚠️ cookies.txt found but invalid format - age-restricted videos may not work")
            print("   Expected Netscape format. Use browser extension or yt-dlp to generate correct format.")
    else:
        print("⚠️ cookies.txt not found - age-restricted videos may not work")
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

if __name__ == "__main__":
    bot.run(TOKEN) 