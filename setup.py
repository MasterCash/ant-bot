from distutils.util import strtobool
from enum import Enum
from multiprocessing import Lock
import sys
import cv2 as cv
from windowManager import findWindow, getWindowInfo
from vision import Vision
from bot import Consts, findIcons

class DataCrop(Enum):
  name = "name"
  id = "id"
  power = "power"
  alliance = "alliance"

def main(window_name: str or None = None, crosshair: bool = False):
  if window_name == None: window_name = "BlueStacks"
  ctrl_name = f"Controls: {window_name}"
  iconCrops = dict([
    (DataCrop.name, Consts.NAME_CROP),
    (DataCrop.id, Consts.ID_CROP),
    (DataCrop.power, Consts.POWER_CROP),
    (DataCrop.alliance, Consts.ALLIANCE_CROP),
  ])

  iconCrops = Consts.iconCrops.copy()

  keys = [icon for icon in iconCrops]
  curIcon = [keys[0]]
  def updateX1(x1):
    _, y1, x2, y2 = iconCrops[curIcon[0]]
    iconCrops[curIcon[0]] = (x1, y1, x2, y2)
  def updateX2(x2):
    x1, y1, _, y2 = iconCrops[curIcon[0]]
    iconCrops[curIcon[0]] = (x1, y1, x2, y2)
  def updateY1(y1):
    x1, _, x2, y2 = iconCrops[curIcon[0]]
    iconCrops[curIcon[0]] = (x1, y1, x2, y2)
  def updateY2(y2):
    x1, y1, x2, _ = iconCrops[curIcon[0]]
    iconCrops[curIcon[0]] = (x1, y1, x2, y2)

  hwnd = findWindow(window_name, "Qt5154QWindowOwnDCIcon")
  capture = getWindowInfo(hwnd, Lock())
  def iconChange(pos):
    curIcon[0] = keys[pos]
    x1, y1, x2, y2 = iconCrops[curIcon[0]]
    cv.setTrackbarPos("x1", ctrl_name, x1)
    cv.setTrackbarPos("y1", ctrl_name, y1)
    if not crosshair:
      cv.setTrackbarPos("x2", ctrl_name, x2)
      cv.setTrackbarPos("y2", ctrl_name, y2)

  stopped = False
  cv.namedWindow(ctrl_name, cv.WINDOW_GUI_EXPANDED)
  cv.resizeWindow(ctrl_name,1200,250)
  x1, y1, x2, y2 = iconCrops[curIcon[0]]
  cv.createTrackbar("icon", ctrl_name, 0, len(keys) - 1, iconChange)
  cv.createTrackbar("x1", ctrl_name, x1, capture.size[0], updateX1)
  cv.createTrackbar("y1", ctrl_name, y1, capture.size[1], updateY1)
  if not crosshair:
    cv.createTrackbar("x2", ctrl_name, x2, capture.size[0], updateX2)
    cv.createTrackbar("y2", ctrl_name, y2, capture.size[1], updateY2)

  while not stopped:
    img = capture.capture()
    if crosshair:
      img2 = Vision.drawCrosshairs(img.copy(), [(iconCrops[curIcon[0]][0], iconCrops[curIcon[0]][1])])
    else:
      img2 = Vision.drawCoordinates(img.copy(), [iconCrops[curIcon[0]]], [curIcon[0].name])
    matches = findIcons(img)
    img2 = Vision.drawRectangles(img2, list(matches.values()))

    cv.imshow(f"setup: {window_name}", img2)
    key = cv.waitKey(1)
    if key == ord("q"):
      stopped = True

    if key == ord('c'):
      crop = Vision.crop(img, iconCrops[curIcon[0]])
      crop = Vision.setGrey(crop)
      cv.imwrite(f'./icons/{curIcon[0].name}-icon.png', crop)
      print(f"saved: {curIcon[0].name} crop")

  for icon in iconCrops:
    print(f'(Icon.{icon.name}, {iconCrops[icon]}),')
  cv.destroyAllWindows()

if __name__ == "__main__":
  if len(sys.argv) > 1:

    try:
      val = strtobool(sys.argv[1])
      main(None, bool(val))
    except ValueError:
      if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
      else:
        main(sys.argv[1])
  else:
    main()