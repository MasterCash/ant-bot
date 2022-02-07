import os
from threading import Thread
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datamanager import DataManager

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("GUILD_NAME")

class dataQuery(commands.Cog):
  DataManager: DataManager
  def __init__(self, dataManager: DataManager) -> None:
      super().__init__()
      self.DataManager = dataManager

  @commands.command()
  async def antName(self, ctx, name: str):
    print(f"user requested {name} data")
    pass
  @commands.command()
  async def antHelp(self, ctx, *, member: discord.Member = None):
    await ctx.send("commands: antName - search for ant hill with given name")
    pass

class DiscordBot(commands.Bot):
  stopped: bool = True
  def __init__(self, command_prefix, dataManager: DataManager):
      super().__init__(command_prefix)
      self.add_cog(dataQuery(dataManager))

  async def on_ready(self):
    print(f"{self.user} has connected")


data = DataManager()

bot = DiscordBot("!", data)
bot.run(TOKEN)
