from datetime import datetime
def get_timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import os




class MyBot(commands.Bot):
    def __init__(self, token):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.token = token

    def start_BOT(self):
        self.run(self.token)




load_dotenv()
bot = MyBot(os.getenv("DISCORD_TOKEN"))

bot.start_BOT()
