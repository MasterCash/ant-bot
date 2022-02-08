from typing import Any
import cv2 as cv
import pyautogui
from time import sleep, time
from threading import Thread, Lock
from vision import Vision


class State:
  Initializing = 0
  InAntHill = 1
  OnMap = 2
  SearchPoint = 3
  RecordInfo = 4
  Unknown = 5
  AtLocation = 6


class Icon:
  info = "info"
  search = "search"
  power = "power"
  x = "x"
  coords = "coords"
  share = "share"
  creature = "creature"
  app = "app"
  rally = "rally"
  ruler = "ruler"
  alliance = "alliance"

class Bot:
  LOADING_SECONDS = 6
  ICON_MATCH_THRESHOLD = 0.8
  HILL_SECONDS = 1
  SLEEP_SECONDS = 0.5

  stopped = True
  screenshotLock = None
  state = None
  screenshot = None
  matches: dict[Icon, tuple[int, int, int, int]] = {}
  timestamp = None
  windowOffset = (0,0)
  windowSize = (0,0)
  icons: dict[Icon, Any] = {}
  infoIcon = None
  searchIcon = None
  powerIcon = None
  xIcon = None
  serverX = int(468 / 2)
  serverY = 0#int(886 / 2)
  previousState = None
  yUpdated = True
  debug = False
  focus = None
  sendData = None
  leavePoint = None
  centerPoint = None
  iconCrops: dict[Icon, tuple[int, int, int, int]] = {}

  def __init__(self, windowOffset, windowSize, debug = False, focus = None, addData = None) -> None:
    self.screenshotLock = Lock()
    self.windowOffset = windowOffset
    self.windowSize = windowSize
    self.icons[Icon.info] = cv.imread('icons/info-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.search] = cv.imread('icons/search-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.power] = cv.imread('icons/power-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.x] = cv.imread('icons/x-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.coords] = cv.imread('icons/enter-coords.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.share] = cv.imread('icons/share-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.creature] = cv.imread('icons/creature-search-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.app] = cv.imread('icons/app-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.rally] = cv.imread('icons/rally-icon.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.ruler] = cv.imread('icons/ruler-text.png', cv.IMREAD_UNCHANGED)
    self.icons[Icon.alliance] = cv.imread('icons/alliance-icon.png', cv.IMREAD_UNCHANGED)

    self.iconCrops[Icon.info] = (80, 470, 240, 610)
    self.iconCrops[Icon.search] = (0, 500, 80, 660)
    self.iconCrops[Icon.power] = (120, 25, 335, 105)
    self.iconCrops[Icon.x] = (395, 65, 445, 115)
    self.iconCrops[Icon.coords] = (135, 585, 330, 640)
    self.iconCrops[Icon.share] = (250, 240, 400, 355)
    self.iconCrops[Icon.creature] = (100, 500, 380, 600)
    self.iconCrops[Icon.app] = (320, 150, 420, 250)
    self.iconCrops[Icon.rally] = (100, 600, 380, 690)
    self.iconCrops[Icon.ruler] = (200, 10, 290, 65)
    self.iconCrops[Icon.alliance] = (340, 105, 390, 180)

    self.state = State.Initializing
    self.timestamp = time()
    self.debug = debug
    self.focus = focus
    self.sendData = addData
    self.leavePoint = (self.windowSize[0] - 10, self.windowSize[1] - 10)
    self.centerPoint = (self.windowSize[0] / 2, self.windowSize[1] / 2)

  def confirmIcon(self, icon, type) -> tuple[bool, tuple[int, int] | None]:
    base = Vision.setGrey(self.screenshot.copy())
    base = Vision.crop(base, self.iconCrops[type])
    results = Vision.find(base, icon, self.ICON_MATCH_THRESHOLD)
    if len(results) > 0:
      results[0][0] += self.iconCrops[type][0]
      results[0][1] += self.iconCrops[type][1]
      return (True, results[0])
    return (False,)

  def getScreenPosition(self, pos):
    return (pos[0] + self.windowOffset[0], pos[1] + self.windowOffset[1])

  def updateScreenshot(self, screenshot):
    self.screenshotLock.acquire()
    self.screenshot = screenshot
    self.screenshotLock.release()

  def updateState(self, state):
    self.previousState = self.state
    self.state = state

  def getMatches(self):
    if not self.debug:
      return []
    matches = list(self.matches.values())
    return matches

  def getCrops(self):
    if not self.debug:
      return []
    crops = list(self.iconCrops.values())
    return crops

  def start(self):
    self.stopped = False
    t = Thread(target=self.run)
    t.start()

  def stop(self):
    self.stopped = True

  def findIcons(self):
    for icon in self.icons:
      img = Vision.setGrey(self.icons[icon].copy())
      found = self.confirmIcon(img, icon)
      if found[0]:
        self.matches[icon] = found[1]
      elif icon in self.matches:
        self.matches.pop(icon)

  def clickPoint(self, point):
    x, y = self.getScreenPosition(point)
    pyautogui.click(x=x, y=y)
    sleep(self.SLEEP_SECONDS)

  def pressKey(self, key):
    if self.focus != None:
      self.focus()
    pyautogui.press(key)
    sleep(self.SLEEP_SECONDS)

  def pressHotKey(self, mod, key):
    if self.focus != None:
      self.focus()
    pyautogui.hotkey(mod, key)
    sleep(self.SLEEP_SECONDS)

  def enterText(self, text):
    if self.focus != None:
      self.focus()
      pyautogui.typewrite(text)
      sleep(self.SLEEP_SECONDS)

  def enterData(self, key, data):
    self.pressKey(key)
    self.pressHotKey("ctrl", "a")
    self.pressKey("backspace")
    self.enterText(str(data))
    self.pressKey("enter")

  def increment(self):
    self.serverX += 1
    if self.serverX > 600:
      self.serverX = 0
      self.yUpdated = True
      self.serverY += 1
      if self.serverY > 600:
        self.serverY = 0
        self.stop()

  def run(self):
    while not self.stopped:
      if self.screenshot is None:
        continue
      self.findIcons()
      if Icon.app in self.matches:
        self.updateState(State.Unknown)

      ### App is loading up ###
      match self.state:

        case State.Initializing:
          if Icon.x in self.matches:
            # need to close the popup
            point = Vision.getClickPoint(self.matches[Icon.x])
            self.clickPoint(point)
          elif Icon.power in self.matches:
            if Icon.search in self.matches:
              self.updateState(State.OnMap)
            else:
              self.updateState(State.InAntHill)

        case State.InAntHill:
          if Icon.power in self.matches:
            if Icon.search in self.matches:
              self.updateState(State.OnMap)
            else:
              self.clickPoint(self.leavePoint)

        case State.OnMap:
          if Icon.search in self.matches:
            self.pressKey("tab")
          elif Icon.coords in self.matches:
            self.updateState(State.SearchPoint)
          elif Icon.power in self.matches:
            self.updateState(State.InAntHill)
          else:
            self.pressKey("space")

        case State.SearchPoint:
          if Icon.coords in self.matches:
            self.enterData("x", str(self.serverX * 2))
            sleep(self.SLEEP_SECONDS)
            if self.yUpdated:
              self.enterData("y", str(self.serverY * 2))
              self.yUpdated = False
              sleep(self.SLEEP_SECONDS)
            self.pressKey("f")
            self.updateState(State.AtLocation)
          else:
            self.state = State.Unknown

        case State.RecordInfo:
          if Icon.ruler in self.matches:
            alliance = Icon.alliance in self.matches
            self.sendData(self.screenshot.copy(), self.serverX, self.serverY, alliance)
            self.pressKey("escape")
            self.increment()
          if Icon.power in self.matches:
            self.updateState(State.OnMap)

        case State.AtLocation:
          if Icon.info in self.matches:
            point = Vision.getClickPoint(self.matches[Icon.info])
            self.clickPoint(point)
          elif Icon.ruler in self.matches:
            self.updateState(State.RecordInfo)
          elif Icon.creature in self.matches or Icon.rally in self.matches:
            self.pressKey("escape")
            self.increment()
            self.updateState(State.OnMap)
            sleep(self.HILL_SECONDS)
          elif Icon.share in self.matches:
            self.increment()
            self.updateState(State.OnMap)
          else:
            self.clickPoint(self.centerPoint)
            sleep(self.HILL_SECONDS)

        case State.Unknown:
          self.yUpdated = True
          if Icon.app in self.matches:
            print("app crashed")
            self.SLEEP_SECONDS += .05
            print("new speed: {}".format(self.SLEEP_SECONDS))
            point = Vision.getClickPoint(self.matches[Icon.app])
            self.clickPoint(point)
            sleep(self.LOADING_SECONDS)
            self.updateState(State.Initializing)
          elif self.previousState is State.InAntHill:
            self.LOADING_SECONDS += 1
            print("longer sleep")
            self.updateState(State.Initializing)
          elif self.previousState is State.OnMap:
            print("longer sleep")
            self.HILL_SECONDS += .5
            self.updateState(State.Initializing)
          else:
            pyautogui.alert("Something went wrong, came from {}: please restart app".format(self.previousState))
            sleep(5)
          self.updateState(State.Initializing)

