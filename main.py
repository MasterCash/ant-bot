from bot import run
from time import sleep, time
from datamanager import collectData
from windowManager import findWindow
from multiprocessing import Lock, Process, SimpleQueue, Value, Array
import signal
from pointCollection import getClusters

captureLock = Lock()

def getMax(x1, x2) -> int:
  return x1 if x1 > x2 else x2

def fillQueue(killSwitch, queue: SimpleQueue):
  clusters, singles = getClusters(8, 10)
  for cluster in clusters:
    if killSwitch.value:
      return
    queue.put((True, cluster))
  for single in singles:
    if killSwitch.value:
      return
    queue.put((False, single))

def main():
  def handleInterrupt(_signal, _frame):
    print("set killswitch")
    killSwitch.value = True
    pass
  dataQueue: SimpleQueue = SimpleQueue()
  captures: list[tuple[str, int or None]] = []
  # add list of window names
  for window in ["BlueStacks", "BlueStacks 1","BlueStacks 2", "BlueStacks 3", "BlueStacks 5"]:
    hwnd = findWindow(window, "Qt5154QWindowOwnDCIcon")
    # ignore windows we don't find
    if hwnd != None:
      captures.append((window, hwnd))

  numCaptures = len(captures)
  stopped = Array('b',[False for _ in range(numCaptures)])
  positions: SimpleQueue = SimpleQueue()


  runTime = time()
  procs: list[Process] = []
  killSwitch = Value('b', False)
  signal.signal(signal.SIGINT, handleInterrupt)
  db = Process(target=collectData, args=(killSwitch, dataQueue), name="database")
  db.start()
  procs.append(db)
  posProc = Process(target=fillQueue, args=(killSwitch, positions), name="Position Queue Filler")
  posProc.start()
  procs.append(posProc)

  for i in range(numCaptures):
    p = Process(target=run, args=(captures[i], captureLock, positions, dataQueue, i, stopped, killSwitch), name=f'runner-{captures[i][0]}')
    p.start()
    procs.append(p)

  while not (all(stopped) or killSwitch.value):
    sleep(5)

  runTime = time() - runTime
  killSwitch.value = True
  print(f"time: {runTime} sec with {numCaptures} instances")

  for p in procs:
    print(f'process: {p.name} joining...')
    if p.is_alive():
      p.join()
      print(f'process: {p.name} joined')


if __name__ == "__main__":
  main()