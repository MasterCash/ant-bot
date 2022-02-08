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
  dataManager: DataManager
  def __init__(self, dataManager: DataManager) -> None:
      super().__init__()
      self.dataManager = dataManager

  @commands.command()
  async def antName(self, ctx, name: str):
    print(f"user requested {name} data")
    results = self.dataManager.getIdFromName(name)
    if results is not None:
      results = self.dataManager.getDataFromId(results)
      msg = f'''****Info****
  Name: {name}
  id: {results[0]}
  alliance: {results[1]}
  power: {results[2]}
  coords: {results[3]}, {results[4]}
  last checked: {results[5]}
      '''
      await ctx.send(msg)
    else:
      await ctx.send(f"unable to find {name}")
    pass
  @commands.command()
  async def antId(self, ctx, id: int):
    results = self.dataManager.getDataFromId(id)
    if results is not None:
      await ctx.send(f"data: {results}")
    else:
      await ctx.send(f"unable to find {id}")
    pass

class DiscordBot(commands.Bot):
  stopped: bool = True
  def __init__(self, command_prefix, dataManager: DataManager):
      super().__init__(command_prefix)
      self.add_cog(dataQuery(dataManager))

  async def on_ready(self):
    print(f"{self.user} has connected")

  def begin(self):
    self.run(TOKEN)

  def stop(self):
    self.close()
class DiscordRunner:
  stopped: bool = True
  bot: DiscordBot
  def __init__(self, dataManager: DataManager) -> None:
      self.bot = DiscordBot("!", dataManager)

  def start(self):
    self.stopped = False
    t = Thread(target=self.run)
    t.start()

  def run(self):
    self.bot.begin()
  def stop(self):
    self.stopped = True
    self.bot.stop()