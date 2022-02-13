import cv2 as cv
from windowManager import getWindowInfo
from vision import Vision
from bot import Consts

iconCrops = Consts.iconCrops.copy()
def updateX1(x1):
  global iconCrops, curIcon, capture
  _, y1, x2, y2 = iconCrops[curIcon]
  iconCrops[curIcon] = (x1, y1, x2, y2)
def updateX2(x2):
  global iconCrops, curIcon, capture
  x1, y1, _, y2 = iconCrops[curIcon]
  iconCrops[curIcon] = (x1, y1, x2, y2)
def updateY1(y1):
  global iconCrops, curIcon, capture
  x1, _, x2, y2 = iconCrops[curIcon]
  iconCrops[curIcon] = (x1, y1, x2, y2)
def updateY2(y2):
  global iconCrops, curIcon, capture
  x1, y1, x2, _ = iconCrops[curIcon]
  iconCrops[curIcon] = (x1, y1, x2, y2)

keys = [icon for icon in iconCrops]
curIcon = keys[0]
capture = getWindowInfo("BlueStacks", "Qt5154QWindowOwnDCIcon")
def iconChange(pos):
  global iconCrops, curIcon, capture
  curIcon = keys[pos]
  x1, y1, x2, y2 = iconCrops[curIcon]
  cv.setTrackbarPos("x1", "Controls", x1)
  cv.setTrackbarPos("x2", "Controls", x2)
  cv.setTrackbarPos("y1", "Controls", y1)
  cv.setTrackbarPos("y2", "Controls", y2)

def main():
  stopped = False
  global iconCrops, curIcon, capture
  cv.namedWindow("Controls", cv.WINDOW_GUI_EXPANDED)
  cv.resizeWindow("Controls",1200,250)
  x1, y1, x2, y2 = iconCrops[curIcon]
  cv.createTrackbar("icon", "Controls", 0, len(keys), iconChange)
  cv.createTrackbar("x1", "Controls", x1, capture.size[0], updateX1)
  cv.createTrackbar("y1", "Controls", y1, capture.size[1], updateY1)
  cv.createTrackbar("x2", "Controls", x2, capture.size[0], updateX2)
  cv.createTrackbar("y2", "Controls", y2, capture.size[1], updateY2)

  while not stopped:
    img = capture.capture()
    img = Vision.drawCoordinates(img, [iconCrops[curIcon]], [curIcon.name])


    cv.imshow("Image", img)

    if cv.waitKey(1) == ord("q"):
      stopped = True

  print(iconCrops.items())
  cv.destroyAllWindows()

if __name__ == "__main__":
  main()