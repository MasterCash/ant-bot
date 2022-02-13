from threading import Lock, Thread
from typing import Any, Callable
import cv2 as cv
import numpy as np
from time import sleep
from vision import Vision
from enum import Enum
import win32con as wcon
from windowManager import CaptureData

# lock used to prevent overlapping input
lock = Lock()

# position object used to hold start, end, and current position.
# it also contains whether or not this position has finished
class Position:
  current: tuple [int, int]
  start: tuple[int, int]
  end: tuple[int, int]
  yUpdated: bool
  finished: bool

  def __init__(self, start: tuple[int, int], max: tuple[int, int]) -> None:
    self.start = start
    self.end = max
    self.current = (start[0], start[1])
    self.yUpdated = True
    self.finished = False

  def increment(self):
    x, y = self.current
    x += 1
    if x > self.end[0]:
      x = self.start[0]
      y += 1
      self.yUpdated = True
      if y > self.end[1]:
        y = self.start[0]
        self.finished = True
    self.current = (x, y)

class State(Enum):
  Initializing = 0
  InAntHill = 1
  OnMap = 2
  SearchPoint = 3
  RecordInfo = 4
  Unknown = 5
  AtLocation = 6

class Action(Enum):
  Click = "Click"
  Non = "Non"
  Key = "Key"
  Data = "Data"
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

class Consts:
  icons: dict[Icon, Any] = dict([
    (Icon.info, cv.imread('icons/info-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.search, cv.imread('icons/search-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.power, cv.imread('icons/power-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.x, cv.imread('icons/x-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.coords, cv.imread('icons/enter-coords.png', cv.IMREAD_UNCHANGED)),
    (Icon.share, cv.imread('icons/share-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.creatureSearch, cv.imread('icons/creature-search-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.creatureAttack, cv.imread('icons/creature-attack-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.app, cv.imread('icons/app-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.rally, cv.imread('icons/rally-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.ruler, cv.imread('icons/ruler-text.png', cv.IMREAD_UNCHANGED)),
    (Icon.alliance, cv.imread('icons/alliance-icon.png', cv.IMREAD_UNCHANGED)),
  ])

  iconCrops: dict[Icon, tuple[int, int, int, int]] = dict([
    (Icon.info, (80, 470, 240, 610)),
    (Icon.search, (0, 500, 80, 660)),
    (Icon.power, (120, 25, 335, 105)),
    (Icon.x, (395, 55, 445, 115)),
    (Icon.coords, (135, 585, 330, 640)),
    (Icon.share, (250, 240, 400, 355)),
    (Icon.creatureSearch, (100, 500, 380, 600)),
    (Icon.creatureAttack, (100, 500, 380, 600)),
    (Icon.app, (320, 150, 420, 250)),
    (Icon.rally, (100, 600, 380, 690)),
    (Icon.ruler, (200, 10, 290, 65)),
    (Icon.alliance, (340, 105, 390, 180)),
  ])

  INPUT_SLEEP = .05
  DATA_SLEEP = .1
  UI_SLEEP = .5
  MACRO_SLEEP = 2
  ICON_MATCH_THRESHOLD = .85
  MAX_REPEAT = 10

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
    icon = Vision.setGrey(Consts.icons[type].copy())
    found = confirmIcon(base, icon, type)
    if found[0]:
      matches[type] = found[1]
  return matches

def processState(state: State, matches: dict[Icon, tuple[int, int, int, int]], windowSize: tuple[int, int]) -> tuple[State, Action, Any]:
  if Icon.app in matches:
    return (State.Initializing, Action.Click, Vision.getClickPoint(matches[Icon.app]))
  match state:
    case State.Initializing:
      if Icon.x in matches:
        point = Vision.getClickPoint(matches[Icon.x])
        return (state, Action.Click, point)
      if Icon.power in matches:
        if Icon.search in matches:
          return (State.OnMap, Action.Non, None)
        return (State.InAntHill, Action.Non, None)

    case State.InAntHill:
      if Icon.power in matches:
        if Icon.search in matches:
          return (State.OnMap, Action.Non, None)
        return(state, Action.Click, getLeavePoint(windowSize))

    case State.OnMap:
      if Icon.search in matches:
        return (state, Action.Key, wcon.VK_TAB)
      if Icon.coords in matches:
        return (State.SearchPoint, Action.Non, None)
      if Icon.power in matches:
        return (State.InAntHill, Action.Non, None)
      return (state, Action.Key, wcon.VK_SPACE)

    case State.SearchPoint:
      if Icon.coords in matches:
        return (state, Action.Data, None)
      if Icon.power in matches:
        return (State.AtLocation, Action.Non, None)
      #return (State.Unknown, Action.Non, None)

    case State.AtLocation:
      if Icon.info in matches:
        point = Vision.getClickPoint(matches[Icon.info])
        return (state, Action.Click, point)
      if Icon.ruler in matches:
        return (State.RecordInfo, Action.Non, None)
      if Icon.creatureSearch in matches or Icon.creatureAttack in matches or Icon.rally in matches:
        return (State.OnMap, Action.Key, wcon.VK_ESCAPE)
      if Icon.share in matches:
        return (State.OnMap, Action.Non, None)
      if Icon.search in matches:
        return (state, Action.Click, getCenterPoint(windowSize))

    case State.RecordInfo:
      if Icon.ruler in matches:
        return (state, Action.Key,wcon.VK_ESCAPE)
      if Icon.power in matches:
        return (State.OnMap, Action.Non, None)

  return (state, Action.Non, None)

def applyAction(prev_state: State, update: tuple[State, Action, Any], cap: CaptureData, pos: Position, shouldSleep: bool):
  state, action, data = update
  if (prev_state == State.InAntHill or prev_state == State.Initializing) and state == State.OnMap:
    pos.yUpdated = True
  if action is not None:
    match action:
      case Action.Click:
        cap.click(data)
        if shouldSleep: sleep(Consts.INPUT_SLEEP)
      case Action.Data:
        cap.select()
        cap.key(ord("X"))
        sleep(Consts.MACRO_SLEEP)
        x = str(pos.current[0] * 2)
        for num in x:
          cap.key(ord(num))
          sleep(Consts.DATA_SLEEP)
        cap.key(wcon.VK_RETURN)
        sleep(Consts.DATA_SLEEP)
        if pos.yUpdated:
          cap.select()
          cap.key(ord("Y"))
          sleep(Consts.MACRO_SLEEP)
          y = str(pos.current[1] * 2)
          for num in y:
            cap.key(ord(num))
            sleep(Consts.DATA_SLEEP)
          cap.key(wcon.VK_RETURN)
          sleep(Consts.DATA_SLEEP)
          pos.yUpdated = False
        cap.key(ord("F"))
        sleep(Consts.DATA_SLEEP)
        pos.increment()
        if shouldSleep: sleep(Consts.INPUT_SLEEP)
      case Action.Key:
        cap.key(data)


def handleState(captureData: CaptureData, loc: tuple[int, int, int, int], sendData: Callable[[np.ndarray, int, int, bool], None], name: str):
  pos = Position((loc[0], loc[1]), (loc[2], loc[3]))
  prevState = [State.Initializing]
  prevAction = [Action.Non]
  count = [0]
  def stateUpdate():
    img = captureData.capture()
    matches = findIcons(img)
    update = processState(prevState[0], matches, captureData.size)
    state, action, data = update
    if (count[0] > Consts.MAX_REPEAT and state == prevState[0] and action == prevAction[0]) or state == State.Unknown:
      print(f"something went wrong, {prevState[0]} is now at {state} and repeated {count[0]} times with action: {action} Data: {data}")
      prevState[0] = State.Initializing
      return pos.finished
    if action == Action.Key and data == "escape" and state == State.RecordInfo:
      sendData(img, pos.current[0], pos.current[1], Icon.alliance in matches)
    applyAction(prevState[0], update, captureData, pos, True)
    sleep(Consts.UI_SLEEP)
    if prevState[0] == state and action == prevAction[0] and state != State.Initializing:
      count[0] += 1
    else: count[0] = 0
    prevState[0] = state
    prevAction[0] = action
    return pos.finished

  return stateUpdate


def start(updater: Callable[[], None], id: int, status: list[bool], killSwitch: list[bool]):
  t = Thread(target=run, args=(updater, id, status, killSwitch))
  t.start()

def run(updater: Callable[[], None], id: int, status: list[bool], killSwitch: list[bool]):
  while not (status[id] or all(killSwitch)):
    status[id] = updater()
