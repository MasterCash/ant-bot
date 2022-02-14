import asyncio
from bot import handleState, start
from time import sleep, time
from datamanager import DataManager
from discordbot import DiscordRunner
from windowManager import CaptureData, getWindowInfo

def splitLocations(num: int, max: tuple[int, int] = (600, 600)) -> list[tuple[int, int, int, int]]:
  chunk = int(max[0] / num)
  extra = ((num * chunk) % max[0]) + 1
  locs = [(chunk * i, 0, (chunk * (i+1)) -1, max[1]) for i in range(num)]
  x1, y1, x2, y2 = locs[num -1]
  locs[num -1] = (x1, y1, x2 + extra, y2)
  return locs

def main():

  database = DataManager()
  database.start()
  discord = DiscordRunner(database)
  captures: list[CaptureData] = []
  # add list of window names
  for window in ["BlueStacks", "BlueStacks 1","BlueStacks 2", "BlueStacks 3"]:
    info = getWindowInfo(window, "Qt5154QWindowOwnDCIcon")
    # ignore windows we don't find
    if info != None:
      captures.append(info)

  numCaptures = len(captures)
  locs = splitLocations(numCaptures)
  stopped = [False for _ in range(numCaptures)]
  killSwitch = [False]

  runTime = time()
  for i in range(numCaptures):
    start(handleState(captures[i], locs[i],database.addData), i, stopped, killSwitch)
  while not all(stopped):
    sleep(10)
  runTime = time() - runTime
  print(f"time: {runTime} sec with {numCaptures} instances")
  killSwitch[0] = True
  asyncio.run(discord.stop())
  database.stop()
if __name__ == "__main__":
  main()