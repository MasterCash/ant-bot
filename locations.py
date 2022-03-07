from multiprocessing import Lock
import cv2 as cv
from windowManager import findWindow, getWindowInfo
from vision import Vision
from bot import Consts

def main():
  hwnd = findWindow("BlueStacks", "Qt5154QWindowOwnDCIcon")
  if not hwnd:
    return
  capture = getWindowInfo(hwnd, Lock())
  stopped = False

  ctrl_name = "pos"
  cv.namedWindow(ctrl_name, cv.WINDOW_GUI_NORMAL)

  curPos = [0,0]

  def updateX(newX):
    curPos[0] = newX

  def updateY(newY):
    curPos[1] = newY

  cv.createTrackbar("x", ctrl_name, 0, capture.size[0], updateX)
  cv.createTrackbar("y", ctrl_name, 0, capture.size[1], updateY)

  locs: list[tuple[int, int]]= [
  (470, 157),
  (386, 235),
  (272, 314),
  (158, 392),
  (386, 92),
  (272, 150),
  (154, 235),
  (441, 281),
  (323, 353),
  (213, 431),
  (437, 431),
  (331, 503),
  (213, 595),
  (444, 595),
  (331, 673)
]
  count = 0
  while not stopped:
    img = capture.capture()
    img = Vision.drawCrosshairs(img, locs)
    img = Vision.drawCrosshairs(img, [(curPos[0], curPos[1])])

    cv.imshow("window", img)

    key = cv.waitKey(1)
    if key == ord("q"):
      stopped = True
    elif key == ord('f'):
      locs.append((curPos[0], curPos[1]))
  print(locs)
  cv.destroyAllWindows()

if __name__ == "__main__":
  main()

"661, 562" "213, 431"
'''
[
  (386, 92), (-6, -4) (0, 0) (0, 0)
  (468, 157), (-6, -2) (0, 2)(0, 1)
  (272, 150), (-4, -4) (2, 0)(1, 0)
  (386, 235), (-4, -2) (2, 2)(1, 1)
  (441, 281), (-4, -1) (2, 3)(1, 2)
  (154, 235), (-2, -4) (4, 0)(2, 0)
  (272, 314), (-2, -2) (4, 2)(2, 1)
  (323, 353), (-2, -1) (4, 3)(2, 2)
  (437, 431), (-2, 1) (4, 5) (2, 3)
  (213, 431), (0, -1) (6, 3) (3, 2)
  (331, 503), (0, 1) (6, 5)  (3, 3)
  (444, 595), (0, 3) (6, 7)  (3, 4)
  (213, 595), (2, 1) (8, 5)  (4, 3)
  (331, 673) (2, 3) (8, 7)   (4, 4)
]
  (158, 392), (0, -2) (6, 2) (3, 1)

'''