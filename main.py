import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from utils.persistent_views import PersistentViewHandler

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX', '!')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable member intents for welcome messages

# Initialize the bot with both prefix and slash command support
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Register persistent views
    view_handler = PersistentViewHandler(bot)
    await view_handler.register_views()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Load cogs
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded extension: {filename[:-3]}')

# Run the bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())