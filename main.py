import asyncio
from typing import Any, Callable, Coroutine
import cv2 as cv
from cv2 import LINE_4
import numpy as np
from bot import handleState

from time import time
from datamanager import DataManager
from discordbot import DiscordRunner
from windowcapture import CaptureData, getWindowInfo
async def main():

  database = DataManager()
  discord = DiscordRunner(database)
  locs: list[tuple[int, int, int, int]] = [
    (0, 0, 399, 399),
    (400, 0, 600, 399),
    (0, 400, 399, 600),
    (400, 400, 600, 600)
  ]

  captures: list[CaptureData] = []
  for window in ["BlueStacks"]:
    captures.append(getWindowInfo(window))

  stateHandlers: list[Coroutine[Any, Any, Callable[[], bool]]] = []
  for i in range(len(captures)):
    stateHandlers.append(handleState(captures[i], locs[i], database.addData))

  stopped = False
  while not stopped:
    stopped = True
    waits: list[asyncio.Task] = []
    for i in range(len(stateHandlers)):
      print("creating task")
      waits.append(asyncio.create_task(stateHandlers[i]()))
    for wait in waits:
      print("awaiting task")
      if not wait.done():
        await wait
      if not wait.result():
        stopped = False
  await discord.stop()

asyncio.run(main())