from sre_constants import MAX_REPEAT
from threading import Lock
from typing import Any, Callable
import cv2 as cv
import numpy as np
import pyautogui
from time import sleep
from vision import Vision
from enum import Enum

from windowcapture import CaptureData
lock = Lock()

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
  creature = "creature"
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
    (Icon.creature, cv.imread('icons/creature-search-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.app, cv.imread('icons/app-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.rally, cv.imread('icons/rally-icon.png', cv.IMREAD_UNCHANGED)),
    (Icon.ruler, cv.imread('icons/ruler-text.png', cv.IMREAD_UNCHANGED)),
    (Icon.alliance, cv.imread('icons/alliance-icon.png', cv.IMREAD_UNCHANGED)),
  ])

  iconCrops: dict[Icon, tuple[int, int, int, int]] = dict([
    (Icon.info, (80, 470, 240, 610)),
    (Icon.search, (0, 500, 80, 660)),
    (Icon.power, (120, 25, 335, 105)),
    (Icon.x, (395, 65, 445, 115)),
    (Icon.coords, (135, 585, 330, 640)),
    (Icon.share, (250, 240, 400, 355)),
    (Icon.creature, (100, 500, 380, 600)),
    (Icon.app, (320, 150, 420, 250)),
    (Icon.rally, (100, 600, 380, 690)),
    (Icon.ruler, (200, 10, 290, 65)),
    (Icon.alliance, (340, 105, 390, 180)),
  ])

  INPUT_SLEEP = .1
  ICON_MATCH_THRESHOLD = .85
  MAX_REPEAT = 100

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

def clickPoint(point: tuple[int, int], captureData: CaptureData, shouldSleep: bool = True):

  x,y = point
  captureData.focus()
  pyautogui.click(x=x, y=y)
  if shouldSleep: sleep(Consts.INPUT_SLEEP)

def pressKey(key: str, focus: Callable, shouldSleep: bool = True):
  focus()
  pyautogui.press(key)
  if shouldSleep: sleep(Consts.INPUT_SLEEP)

def pressHotKey(mod: str, key: str, focus: Callable, shouldSleep: bool = True):
  focus()
  pyautogui.hotkey(mod, key)
  if shouldSleep: sleep(Consts.INPUT_SLEEP)

def enterText(text: str, focus: Callable, shouldSleep: bool = True):
  focus()
  pyautogui.typewrite(text)
  if shouldSleep: sleep(Consts.INPUT_SLEEP)

def enterData(key, data, focus: Callable, shouldSleep: bool = True):
  pressKey(key, focus, shouldSleep)
  pressHotKey("ctrl", "a", focus, shouldSleep)
  pressKey("backspace", focus, shouldSleep)
  enterText(str(data), focus, shouldSleep)
  pressKey("enter", focus, shouldSleep)

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
        return (state, Action.Key, "tab")
      if Icon.coords in matches:
        return (State.SearchPoint, Action.Non, None)
      if Icon.power in matches:
        return (State.InAntHill, Action.Non, None)
      return (state, Action.Key, "space")

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
      if Icon.creature in matches or Icon.rally in matches:
        return (State.OnMap, Action.Key, "escape")
      if Icon.share in matches:
        return (State.OnMap, Action.Non, None)
      if Icon.search in matches:
        return (state, Action.Click, getCenterPoint(windowSize))

    case State.RecordInfo:
      if Icon.ruler in matches:
        return (state, Action.Key, "escape")
      if Icon.power in matches:
        return (state, Action.Non, None)

  return (state, Action.Non, None)

def increment(pos: Position):
  x, y = pos.current
  x += 1
  if x > pos.end[0]:
    x = 0
    y += 1
    pos.yUpdated = True
    if y > pos.end[1]:
      y = 0
      pos.finished = 0
  pos.current = (x, y)

def applyAction(update: tuple[State, Action, Any], captureData: CaptureData, pos: Position, shouldSleep: bool):
  state, action, data = update
  if action is not None:
    match action:
      case Action.Click:
        clickPoint(captureData.screenPoint(data), captureData, shouldSleep)
        sleep(Consts.INPUT_SLEEP)
      case Action.Data:
        enterData("x", pos.current[0], captureData.focus, shouldSleep)
        if pos.yUpdated:
          enterData("y", pos.current[0], captureData.focus, shouldSleep)
        pressKey("f", captureData.focus, shouldSleep)
        increment(pos)
      case Action.Key:
        pressKey(data, captureData.focus, shouldSleep)


def handleState(captureData: CaptureData, loc: tuple[int, int, int, int], sendData: Callable[[np.ndarray, int, int, bool], None]):
  print("getting state updater")
  pos = Position((loc[0], loc[1]), (loc[2], loc[3]))
  prevState = [State.Initializing]
  count = [0]
  async def stateUpdate():
    print("running state updater")
    img = captureData.capture()
    matches = findIcons(img)
    update = processState(prevState[0], matches, captureData.size)
    state, action, data = update
    if action == Action.Key and data == "escape" and state == State.RecordInfo:
      sendData(img, pos.current[0], pos.current[1], Icon.alliance in matches)
    lock.acquire()
    applyAction(update, captureData, pos, True)
    lock.release()
    if prevState[0] is state and state != State.Initializing:
      count[0] += 1
    else: count[0] = 0
    if count[0] > Consts.MAX_REPEAT or state == State.Unknown:
      pyautogui.alert(f"something went wrong, {prevState[0]} is now at {state} and repeated {count[0]} times")
      prevState[0] = State.Initializing
    prevState[0] = state
    return pos.finished

  return stateUpdate