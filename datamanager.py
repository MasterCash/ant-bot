from queue import  Empty
from multiprocessing import SimpleQueue
import signal
import sqlite3
from time import sleep

class Data:
  state: int
  id: int
  power: int
  alliance: str or None
  name: str
  loc: tuple[int, int]

class DataManager:

  file_name = "db.sqlite"

  def __init__(self) -> None:
    con = self.getCon()
    with con:
      con.execute('''CREATE TABLE IF NOT EXISTS ant_hills
        (id INTEGER PRIMARY KEY NOT NULL,
        power INTEGER NOT NULL,
        x INTEGER NOT NULL, y INTEGER NOT NULL,
        time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (x, y))''')
      con.execute('''CREATE TABLE IF NOT EXISTS id_names
        (id INTEGER NOT NULL REFERENCES ant_hills (id) ON DELETE CASCADE ON UPDATE CASCADE,
         name TEXT NOT NULL,
         time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
         PRIMARY KEY(id, name))''')
      con.execute('''CREATE TABLE IF NOT EXISTS id_alliances
        (id INTEGER NOT NULL REFERENCES ant_hills (id) ON DELETE CASCADE ON UPDATE CASCADE,
         name TEXT,
         time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
         PRIMARY KEY(id, name))''')
    con.close()

  def getCon(self):
    return sqlite3.connect(self.file_name)




  def getIdFromName(self, name):
    con = self.getCon()
    with con:
      cur = con.execute('''
      SELECT id FROM id_names WHERE name IS ?
      ''', (name,))
      result = cur.fetchone()
      return result[0] if result != None else None

  def getDataFromId(self, uid):
    con = self.getCon()
    with con:
      cur = con.execute('''
      SELECT * FROM ant_hills WHERE id IS ?
      ''', (str(uid),))
      result = cur.fetchone()
      return result


  def sendData(self, uid, name, alliance, power, x, y):
    con = self.getCon()
    if uid is None or not uid:
      uid = "None"
    if name is None or not name:
      name = "None"
    if power is None:
      power = 0
    if x is None:
      x = -1
    if y is None:
      y = -1

    try:
      with con:
        con.execute('''
        INSERT OR REPLACE INTO ant_hills (id, power, x, y)
        VALUES (?, ?, ?, ?)
        ''',(uid, power, x, y))
        con.execute('''
        INSERT OR REPLACE INTO id_names (id, name)
        VALUES (?, ?)
        ''', (uid, name))
        con.execute('''
          INSERT OR REPLACE INTO id_alliances (id, name)
          VALUES (?, ?)
        ''', (uid, alliance))
    except:
      print(f'error entering: {uid}, {name}, {alliance}, {power}, {x}, {y}')
    con.close()

def collectData(killswitch, dataQueue: SimpleQueue):
  signal.signal(signal.SIGINT, signal.SIG_IGN)
  database = DataManager()
  while not (killswitch.value and dataQueue.empty()):
    try:
      if not dataQueue.empty():
        (uid, name, alliance, power, x, y)= dataQueue.get()
        database.sendData(uid, name, alliance, power, x, y)
      sleep(5)
    except Empty:
      pass
  dataQueue.close()