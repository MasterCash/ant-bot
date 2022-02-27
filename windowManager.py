from multiprocessing import synchronize
from time import sleep
from typing import Callable
import numpy as np
import win32gui as wgui, win32ui as wui, win32con as wcon, win32api as wapi
from pygetwindow import Win32Window

class CaptureData:
  capture: Callable[[], np.ndarray]
  click: Callable[[tuple[int, int]], None]
  size: tuple[int, int]
  key: Callable[[int], None]
  delete: Callable[[], None]
  hwnd: int
  window_name: str

  def copy(self, data: 'CaptureData'):
    self.capture = data.capture
    self.click = data.click
    self.size = data.size
    self.key = data.key
    self.delete = data.delete
    self.hwnd = data.hwnd
    self.window_name = data.window_name


def findWindow(windowName: str, className:str or None = None) -> int or None:
  hwnd = wgui.FindWindow(className, windowName)
  return None if not hwnd else hwnd

def getWindowInfo(hwnd: int, lock: synchronize.Lock, offset: tuple[int, int, int, int] = (0,35,35,0)):
  if not hwnd:
    return None
  windowName = wgui.GetWindowText(hwnd)
  Win32Window(hwnd).size = (575, 1000)
  windowRect = wgui.GetWindowRect(hwnd)
  w = windowRect[2] - windowRect[0]
  h = windowRect[3] - windowRect[1]
  w = w - (offset[0] + offset[1])
  h = h - (offset[2] + offset[3])
  croppedX = offset[0]
  croppedY = offset[2]

  def getCapture():
    # get the window image data
    try:
      lock.acquire()
      wDC = wgui.GetWindowDC(hwnd)
      dcObj = wui.CreateDCFromHandle(wDC)
      cDC = dcObj.CreateCompatibleDC()
      dataBitMap = wui.CreateBitmap()
      dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
      cDC.SelectObject(dataBitMap)
      cDC.BitBlt((0, 0), (w, h), dcObj, (croppedX, croppedY), wcon.SRCCOPY)

      # convert the raw data into a format opencv can read
      signedIntsArray = dataBitMap.GetBitmapBits(True)

      # free resources
      dcObj.DeleteDC()
      cDC.DeleteDC()
      wgui.ReleaseDC(hwnd, wDC)
      wgui.DeleteObject(dataBitMap.GetHandle())
    finally:
      lock.release()


    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (h, w, 4)
    # drop the alpha channel, or cv.matchTemplate() will throw an error like:
    #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type()
    #   && _img.dims() <= 2 in function 'cv::matchTemplate'
    #img = img[...,:3]
    img = np.ascontiguousarray(img)
    return img

  # BlueStacks' input window
  hwndChild = wgui.GetWindow(hwnd, wcon.GW_CHILD)

  def mouseClick(point: tuple[int, int]):
    x, y = point
    lParam = wapi.MAKELONG(int(x), int(y))
    wapi.PostMessage(hwndChild, wcon.WM_LBUTTONDOWN, wcon.MK_LBUTTON, lParam)
    wapi.PostMessage(hwndChild, wcon.WM_LBUTTONUP, wcon.MK_LBUTTON, lParam)

  #lparam for KEYDOWN/KEYUP events

  keyUp = ((0xc0 << 24)|(0x11 << 16)|1)
  keyDown = ((0x00 << 24)|(0x11 << 16)|1)

  def keyPress(key: int):
    # bluestacks disables game control whenever window inactive: https://stackoverflow.com/a/65330005
    wapi.SendMessage(hwnd, wcon.WM_ACTIVATE, wcon.WA_CLICKACTIVE, 0)
    wapi.PostMessage(hwndChild, wcon.WM_KEYDOWN, key, keyDown)
    sleep(.1)
    wapi.PostMessage(hwndChild, wcon.WM_KEYUP, key, keyUp)

  def deleteAll():
    wapi.SendMessage(hwnd, wcon.WM_ACTIVATE, wcon.WA_CLICKACTIVE, 0)
    wapi.PostMessage(hwndChild, wcon.WM_KEYDOWN, wcon.VK_BACK, keyDown)
    wapi.PostMessage(hwndChild, wcon.WM_KEYUP, wcon.VK_BACK, keyUp)
    sleep(.05)
    wapi.PostMessage(hwndChild, wcon.WM_KEYDOWN, wcon.VK_BACK, keyDown)
    wapi.PostMessage(hwndChild, wcon.WM_KEYUP, wcon.VK_BACK, keyUp)
    sleep(.05)
    wapi.PostMessage(hwndChild, wcon.WM_KEYDOWN, wcon.VK_BACK, keyDown)
    wapi.PostMessage(hwndChild, wcon.WM_KEYUP, wcon.VK_BACK, keyUp)
    sleep(.05)
    wapi.PostMessage(hwndChild, wcon.WM_KEYDOWN, wcon.VK_BACK, keyDown)
    wapi.PostMessage(hwndChild, wcon.WM_KEYUP, wcon.VK_BACK, keyUp)

  data: CaptureData = CaptureData()
  data.capture = getCapture
  data.click = mouseClick
  data.key = keyPress
  data.delete = deleteAll
  data.size = (w, h)
  data.hwnd = hwnd
  data.window_name = windowName

  return data