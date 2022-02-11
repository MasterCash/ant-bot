from threading import Lock
from typing import Callable
import numpy as np
import win32gui, win32ui, win32con

lock: Lock = Lock()
class CaptureData:
  capture: Callable[[], np.ndarray]
  focus: Callable[[], None]
  screenPoint: Callable[[tuple[int, int]], tuple[int, int]]
  size: tuple[int, int]

def getWindowInfo(windowName: str, offset: tuple[int, int, int, int] = (0,35,35,0)):
  hwnd = win32gui.FindWindow(None, windowName)
  if not hwnd:
    return None

  windowRect = win32gui.GetWindowRect(hwnd)
  w = windowRect[2] - windowRect[0]
  h = windowRect[3] - windowRect[1]
  w = w - (offset[0] + offset[1])
  h = h - (offset[2] + offset[3])
  croppedX = offset[0]
  croppedY = offset[2]
  windowOffset = (windowRect[0] + croppedX, windowRect[1] + croppedY)

  def getCapture():
    # get the window image data
    lock.acquire()
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (w, h), dcObj, (croppedX, croppedY), win32con.SRCCOPY)

    # convert the raw data into a format opencv can read
    signedIntsArray = dataBitMap.GetBitmapBits(True)

    # free resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    lock.release()

    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (h, w, 4)
    img = np.ascontiguousarray(img)
    return img

  def getFocus():

    try:
        win32gui.SetForegroundWindow(hwnd)
    except:
        pass

  def getScreenPosition(point: tuple[int, int]) -> tuple[int, int]:
    return (point[0] + windowOffset[0], point[1] + windowOffset[1])
  data: CaptureData = CaptureData()
  data.capture = getCapture
  data.focus = getFocus
  data.screenPoint = getScreenPosition
  data.size = (w, h)

  return data