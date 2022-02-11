import asyncio
from bot import handleState, start

from time import sleep, time
from datamanager import DataManager
from discordbot import DiscordRunner
from windowcapture import CaptureData, getWindowInfo

def main():

  database = DataManager()
  discord = DiscordRunner(database)
  locs: list[tuple[int, int, int, int]] = [
    (0, 0, 399, 399),
    (400, 0, 600, 399),
    (0, 400, 399, 600),
    (400, 400, 600, 600)
  ]

  captures: list[CaptureData] = []
  # add list of window names
  for window in ["BlueStacks 2", ]:
    captures.append(getWindowInfo(window))
  numCaptures = len(captures)
  stopped = list(map(lambda x: False, range(numCaptures)))
  killSwitch = [False]
  runTime = time()
  for i in range(numCaptures):
    start(handleState(captures[i], locs[i],database.addData, str(i)), i, stopped, killSwitch)
  while not all(stopped):
    sleep(10)
  runTime = time() - runTime
  print(f"time: {runTime} sec with {numCaptures} instances")
  killSwitch[0] = True
  asyncio.run(discord.stop())

if __name__ == "__main__":
  main()