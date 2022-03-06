from multiprocessing import Process, SimpleQueue
import signal
from threading import Lock
from typing import Any, Callable
import cv2 as cv
import numpy as np
from time import sleep
from vision import Vision
from enum import Enum
import win32con as wcon
from windowManager import CaptureData, findWindow, getWindowInfo

Point = tuple[int, int]

# lock used to prevent overlapping input
lock = Lock()

class Icon(Enum):
  info = "info"
  search = "search"
  power = "power"
  x = "x"
  coords = "coords"
  share = "share"
  creatureSearch = "creature-search"
  creatureAttack = "creature-attack"
  app = "app"
  rally = "rally"
  ruler = "ruler"
  alliance = "alliance"
  #loading = "loading"

class States(Enum):
  Startup = "Startup"
  InHill = "InHill"
  OnMap = "OnMap"
  Unknown = "Unknown"
  StartSearch = "StartSearch"
  AtPosition = "AtPosition"
  NextPosition = "NextPosition"
  GatherInfo = "GatherInfo"
  Done = "Done"

class Actions(Enum):
  Non = "None"
  Click = "Click"
  KeyPress = "KeyPress"
  Wait = "Wait"
  ChangeState = "StateChange"
  EnterData = "EnterData"
  NextPosition = "NextPosition"
  Collect = "Collect"
  NewPoint = "NewPoint"

ActionInfo = tuple[Actions, Any]
Box = tuple[int, int, int, int]

class Prev:
  state: States = States.Startup
  action: Actions = Actions.Non
  curPosition: tuple[bool, Point] = None
  index: int = 0
  count: int = 0

class Consts:
  icons: dict[Icon, np.ndarray] = dict([(icon, cv.imread(f'icons/{icon.name}-icon.png', cv.IMREAD_GRAYSCALE)) for icon in Icon])

  iconCrops: dict[Icon, tuple[int, int, int, int]] = dict([
    (Icon.info, (0, 0, 509, 701)),
    (Icon.search, (0, 586, 80, 666)),
    (Icon.power, (171, 25, 244, 82)),
    (Icon.x, (456, 59, 515, 130)),
    (Icon.coords, (152, 665, 393, 742)),
    (Icon.share, (284, 284, 470, 403)),
    (Icon.creatureSearch, (132, 584, 408, 683)),
    (Icon.creatureAttack, (132, 584, 408, 683)),
    (Icon.app, (389, 193, 476, 307)),
    (Icon.rally, (147, 715, 409, 795)),
    (Icon.ruler, (245, 12, 326, 51)),
    (Icon.alliance, (406, 117, 450, 174)),
    #(Icon.loading, (0, 0, 509, 701)),
  ])

  clickPoints: dict[int, dict[int, tuple[int, int]]] = dict({
    0: dict({
      0: (386, 92),
      1: (468, 157),
    }),

    1: dict({
      0: (272, 150),
      1: (286, 235),
      2: (441, 281),
    }),

    3: dict({
      2: (213, 431),
      3: (331, 503),
      4: (444, 595),
    }),

    4: dict({
      3: (213, 595),
      4: (331, 673),
    }),
  })


  pointLocations: list[tuple[int, int]] = [
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
    (1, 2),
    (3, 2),
    (3, 3),
    (3, 4),
    (4, 3),
    (4, 4),
  ]
  POINT_OFFSET = (6, 4)
  INPUT_SLEEP = .05
  DATA_SLEEP = .1
  UI_SLEEP = .5
  MACRO_SLEEP = 2
  LOADING_SLEEP = 5
  ICON_MATCH_THRESHOLD = .8
  MAX_REPEAT = 10
  NAME_CROP = (162, 96, 395, 121)
  ID_CROP = (331, 211, 407, 232)
  POWER_CROP = (395, 245, 505, 266)
  ALLIANCE_CROP = (163, 134, 396, 156)


def getLeavePoint(windowSize: tuple[int, int]):
  return (windowSize[0] - 10, windowSize[1] - 10)

def getCenterPoint(windowSize: tuple[int, int]):
  return (windowSize[0] / 2, windowSize[1] / 2)

def confirmIcon(img, icon, type) -> tuple[bool, tuple[int, int] | None]:
    base = Vision.setGrey(img.copy())
    base = Vision.crop(base, Consts.iconCrops[type])
    results = Vision.find(base, icon, Consts.ICON_MATCH_THRESHOLD)
    if len(results) > 0:
      results[0][0] += Consts.iconCrops[type][0]
      results[0][1] += Consts.iconCrops[type][1]
      return (True, results[0])
    return (False, None)

def findIcons(base) -> dict[Icon, tuple[int, int, int, int]]:
  matches = {}
  for type in Consts.icons:
    icon = Consts.icons[type].copy()
    found = confirmIcon(base, icon, type)
    if found[0]:
      matches[type] = found[1]
  return matches

def clickPoint(point: Box) -> Point:
  return Vision.getClickPoint(point)

def relativePoint(prev: Prev):
  x, y = prev.curPosition[1]
  offX, offY = Consts.pointLocations[prev.index]
  return (x + offX, y + offY)

def indexPoint(index: int):
  point = Consts.pointLocations[index]
  return Consts.clickPoints[point[0]][point[1]] #Consts.clickPoints[point[0]][point[1]]

def posStr(prev: Prev) -> tuple[str, str]:
  posType, pos = prev.curPosition
  x = pos[0]
  y = pos[1]

  if posType:
    offX, offY = Consts.POINT_OFFSET
    x += offX
    y += offY

  return (str(x), str(y))


def processState(prev: Prev, matches: dict[Icon, Box], windowSize: Point) -> ActionInfo:

  match prev.state:
    case States.Startup:
      if Icon.app in matches:
        return (Actions.Click, clickPoint(matches[Icon.app]))
      if Icon.x in matches:
        if prev.action != Actions.Click:
          return (Actions.Click, clickPoint(matches[Icon.x]))
      if Icon.loading in matches:
        return (Actions.Wait, Consts.LOADING_SLEEP)
      if Icon.power in matches:
        return (Actions.ChangeState, States.InHill)

    case States.InHill:
      if Icon.search in matches:
        return (Actions.ChangeState, States.OnMap)
      if Icon.power in matches:
        if prev.action != Actions.Click:
          return (ActionInfo.Click, getLeavePoint(windowSize))
      if prev.action != Actions.Wait:
        return (Actions.Wait, Consts.LOADING_SLEEP)
      return (Actions.ChangeState, States.Unknown)

    case States.OnMap:
      if Icon.coords in matches:
        return (Actions.ChangeState, States.StartSearch)
      if Icon.search in matches:
        if prev.action != Actions.KeyPress:
          return (Actions.KeyPress, wcon.VK_TAB)
      if Icon.power not in matches and prev.action is Actions.KeyPress:
        return (Actions.KeyPress, wcon.VK_SPACE)

    case States.StartSearch:
      if Icon.coords in matches:
        return (Actions.EnterData, None)
      if Icon.search in matches:
        return (Actions.ChangeState, States.AtPosition)
      return (Actions.ChangeState, States.Unknown)

    case States.AtPosition:
      if Icon.ruler in matches:
        return (Actions.ChangeState, States.GatherInfo)
      if Icon.info in matches:
        if prev.action != Actions.Click:
          return (Actions.Click, clickPoint[Icon.info])
      else:
        if prev.action != Actions.Click:
          if prev.curPosition[0]:
            return (Actions.Click, indexPoint(prev.index))
          else:
            return (Actions.Click, getCenterPoint(windowSize))
        else:
          return (Actions.Wait, Consts.UI_SLEEP)

    case States.GatherInfo:
      if Icon.ruler in matches:
        if prev.action == Actions.Collect:
          return (Actions.KeyPress, wcon.VK_ESCAPE)
        else:
          return (Actions.Collect, relativePoint(prev))
      if Icon.search in matches:
        return (Actions.ChangeState, States.NextPosition)

    case States.NextPosition:
      if prev.curPosition is not None:
        if (prev.curPosition[0] and prev.index == len(Consts.pointLocations)) or not prev.curPosition[0]:
          return (Actions.NewPoint, None)
        if prev.action == Actions.NextPosition:
          return (Actions.ChangeState, States.AtPosition)
        return (Actions.NextPosition, None)
      return (Actions.ChangeState, States.Done)

  if Icon.app in matches:
    return (Actions.ChangeState, States.Startup)

  return (Actions.Non, None)

def applyAction(prev: Prev, update: ActionInfo, cap: CaptureData, posQueue: SimpleQueue, dataQueue: SimpleQueue, img: np.ndarray, matches: dict[Icon, Box]) -> None:
  action, data = update
  match action:
    case Actions.Non:
      pass

    case Actions.Click:
      cap.click(data)

    case Actions.KeyPress:
      cap.key(data)

    case Actions.Wait:
      sleep(data)

    case Actions.ChangeState:
      prev.state = data
      prev.action = action

    case Actions.EnterData:
      x, y = posStr(prev)
      cap.key(ord('X'))
      sleep(Consts.DATA_SLEEP)
      cap.delete()
      sleep(Consts.DATA_SLEEP)

      # X coord
      for char in x:
        cap.key(ord(char))
        sleep(Consts.DATA_SLEEP)
      cap.key(wcon.VK_RETURN)
      sleep(Consts.DATA_SLEEP)

      # Y coord
      for char in y:
        cap.key(ord(char))
        sleep(Consts.DATA_SLEEP)
      cap.key(wcon.VK_RETURN)
      sleep(Consts.DATA_SLEEP)

      cap.key(ord("F"))
      sleep(Consts.DATA_SLEEP)

    case Actions.NextPosition:
      prev.index += 1

    case Actions.Collect:
      p = Process(target=handleText, args=(dataQueue, img, data, Icon.alliance in matches))
      p.start()

    case Actions.NewPoint:
      if posQueue.empty():
        prev.curPosition = None
        prev.index = 0
      else:
        prev.curPosition = posQueue.get()
        prev.index = 0

def handleState(captureData: CaptureData, positions: SimpleQueue[tuple[bool, Point]], dataQueue: SimpleQueue):
  prev: Prev = Prev()
  name = captureData.window_name
  if not positions.empty():
    prev.curPosition = positions.get()

  def updateState() -> bool:
    img = captureData.capture()
    matches = findIcons(img)
    actionInfo = processState(prev.state, prev.action, matches, captureData.size)
    action, data = actionInfo
    print(f"<< {name}: at {prev.state} with action: {action} Data: {data}")

    if action == prev.action:
      prev.count += 1
    else:
      prev.count = 0
    if prev.count >= Consts.MAX_REPEAT:
      print(f" << {name} hit repeat threshold on state {prev.state}.")
      print(f" << << state: {prev.state}")
      print(f" << << action: {prev.action}")
      print(f" << << pos: {prev.curPosition}")
      print(f" << << index: {prev.index}")
      print(f" << << nextAction: {actionInfo}")
      print(f" << << matches: {matches}")
      prev.state = States.Startup
      prev.action = Actions.ChangeState
    else:
      applyAction(prev, actionInfo, captureData, positions, dataQueue, img, matches)

    return prev.curPosition is not None


  return updateState

def run(windowInfo: tuple[str, int], captureLock: Lock, positions: SimpleQueue[tuple[bool, Point]], dataQueue: SimpleQueue, id: int, status: list[bool], killSwitch: Any):
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  windowName, hwnd = windowInfo
  captureData = getWindowInfo(hwnd, captureLock)
  updater = handleState(captureData, positions, dataQueue)
  while not(status[id] or killSwitch.value):
    if hwnd == None:
      sleep(5)
      hwnd = findWindow(windowName, "Qt5154QWindowOwnDCIcon")
      if hwnd != None:
        captureData.copy(getWindowInfo(hwnd, captureLock))
        continue
    try:
      status[id] = updater()
    except Exception as ex:
      print(f" << window {windowName} handling Exception: {type(ex).__name__}, args: {ex.args}")
      if ex.args[0] == 1400:
        hwnd = None


def handleText(dataQueue: SimpleQueue, img: np.ndarray, point: Point, hasAlliance: bool) -> None:
  img = Vision.setGrey(img)
  nameImg = Vision.crop(img, Consts.NAME_CROP)
  name = Vision.findText(nameImg)
  alliance: str = None
  if hasAlliance:
    allianceImg = Vision.crop(img, Consts.ALLIANCE_CROP)
    alliance = Vision.findText(allianceImg)
    if alliance is not None:
      alliance[0] = '['
      alliance[3] = ']'

  idImg = Vision.crop(img, Consts.ID_CROP)
  uid = Vision.findText(idImg)
  powerImg = Vision.crop(img, Consts.POWER_CROP)
  power = Vision.findText(powerImg)
  dataQueue.put((uid, name, alliance, power, point[0], point[1]))