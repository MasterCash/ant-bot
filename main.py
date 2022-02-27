from numpy import maximum
from bot import handleState, run
from time import sleep, time
from datamanager import DataManager, collectData
from windowManager import CaptureData, findWindow, getWindowInfo
from multiprocessing import Lock, Process, SimpleQueue, Value, Array
import signal

def splitLocations(num: int, max: tuple[int, int] = (600, 600)) -> list[tuple[int, int, int, int]]:
  if num == 0:
    return [(0, 0, max[0], max[1])]
  chunk = getMax(int((max[0] + 1) / num), 1)
  extra = (max[0] - (num * chunk)) + 1
  locs = [(chunk * i, 0, (chunk * (i+1)) -1, max[1]) for i in range(num)]
  x1, y1, x2, y2 = locs[num -1]
  locs[num -1] = (x1, y1, x2 + extra, y2)
  return locs


captureLock = Lock()

def getMax(x1, x2) -> int:
  return x1 if x1 > x2 else x2

def main():
  def handleInterrupt(_signal, _frame):
    print("set killswitch")
    killSwitch.value = True
    pass
  dataQueue: SimpleQueue = SimpleQueue()
  captures: list[CaptureData] = []
  # add list of window names
  for window in ["BlueStacks", "BlueStacks 1","BlueStacks 2", "BlueStacks 3", "BlueStacks 5"]:
    info = findWindow(window, "Qt5154QWindowOwnDCIcon")
    # ignore windows we don't find
    if info != None:
      captures.append(info)

  numCaptures = len(captures)
  locs = splitLocations(numCaptures)#, (0,9))
  print(locs)
  stopped = Array('b',[False for _ in range(numCaptures)])

  runTime = time()
  procs: list[Process] = []
  killSwitch = Value('b', False)
  db = Process(target=collectData, args=(killSwitch, dataQueue))
  db.start()
  procs.append(db)
  for i in range(numCaptures):

    p = Process(target=run, args=(captures[i], captureLock, locs[i], dataQueue, i, stopped, killSwitch))
    p.start()
    procs.append(p)
  signal.signal(signal.SIGINT, handleInterrupt)

  while not (all(stopped) or killSwitch.value):
    sleep(5)

  runTime = time() - runTime
  killSwitch.value = True
  print(f"time: {runTime} sec with {numCaptures} instances")

  for p in procs:
    if p.is_alive():
      p.join()


if __name__ == "__main__":
  main()