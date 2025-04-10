import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the bot token from the .env file
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello there!')

# Run the bot using the token from the .env file
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: BOT_TOKEN is not set in the .env file.")