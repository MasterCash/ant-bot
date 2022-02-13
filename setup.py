from enum import Enum
import sys
import cv2 as cv
from windowManager import getWindowInfo
from vision import Vision
from bot import Consts, findIcons
from datamanager import DataManager
class DataCrop(Enum):
  name = "name"
  id = "id"
  power = "power"
  alliance = "alliance"



def main(window_name: str or None = None):
  if window_name == None: window_name = "BlueStacks"
  ctrl_name = f"Controls: {window_name}"
  iconCrops = dict([
    (DataCrop.name,DataManager.nameCrop),
    (DataCrop.id,DataManager.idCrop),
    (DataCrop.power,DataManager.powerCrop),
    (DataCrop.alliance,DataManager.allianceCrop),
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

  capture = getWindowInfo(window_name, "Qt5154QWindowOwnDCIcon")
  def iconChange(pos):
    curIcon[0] = keys[pos]
    x1, y1, x2, y2 = iconCrops[curIcon[0]]
    cv.setTrackbarPos("x1", ctrl_name, x1)
    cv.setTrackbarPos("x2", ctrl_name, x2)
    cv.setTrackbarPos("y1", ctrl_name, y1)
    cv.setTrackbarPos("y2", ctrl_name, y2)

  stopped = False
  cv.namedWindow(ctrl_name, cv.WINDOW_GUI_EXPANDED)
  cv.resizeWindow(ctrl_name,1200,250)
  x1, y1, x2, y2 = iconCrops[curIcon[0]]
  cv.createTrackbar("icon", ctrl_name, 0, len(keys) - 1, iconChange)
  cv.createTrackbar("x1", ctrl_name, x1, capture.size[0], updateX1)
  cv.createTrackbar("y1", ctrl_name, y1, capture.size[1], updateY1)
  cv.createTrackbar("x2", ctrl_name, x2, capture.size[0], updateX2)
  cv.createTrackbar("y2", ctrl_name, y2, capture.size[1], updateY2)

  while not stopped:
    img = capture.capture()
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
    main(sys.argv[1])
  else:
    main()