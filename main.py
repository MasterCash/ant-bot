import cv2 as cv
from cv2 import LINE_4
import numpy as np
from bot import Bot

from windowcapture import WindowCapture
from vision import Vision
from time import time
from datamanager import DataManager
from discordbot import DiscordRunner

wincap = WindowCapture("BlueStacks")
dm = DataManager()
bot = Bot(wincap.getOffset(), wincap.getSize(), True, focus=wincap.setFocus, addData=dm.addData)
discord = DiscordRunner(dm)
wincap.start()
bot.start()
dm.start()
discord.start()
loop_time = time()

while(True):
  if wincap.screenshot is None:
    continue
  bot.updateScreenshot(wincap.screenshot)
  if cv.waitKey(1) == ord('q') or bot.stopped:
    wincap.stop()
    bot.stop()
    cv.destroyAllWindows()
    break
  img = Vision.drawRectangles(np.copy(wincap.screenshot), bot.getMatches())
  img = Vision.drawCoordinates(img, bot.getCrops(), list(bot.iconCrops.keys()))
  #img = Vision.drawCoordinates(img, [dm.nameCrop, dm.powerCrop, dm.allianceCrop, dm.idCrop], ["name", "power", "alliance", "id"])
  cv.imshow("Matches", img)
  print("FPS {}".format(1 /(time() - loop_time)))
  loop_time = time()

print('done')
wincap.stop()
bot.stop()
dm.stop()
discord.stop()
cv.destroyAllWindows()


