from queue import SimpleQueue, Empty
from threading import Thread
import sqlite3
from vision import Vision

class Data:
  state: int
  id: int
  power: int
  alliance: str or None
  name: str
  loc: tuple[int, int]

class DataManager:
  dataQueue: SimpleQueue
  stopped = True
  nameCrop = (140,80,340,110)
  allianceCrop = (140,110,340,144)
  powerCrop = (316,210,435,230)
  idCrop = (284,180,347,210)

  def __init__(self) -> None:
    self.dataQueue = SimpleQueue()
    con = self.getCon()
    with con:
      con.execute('''CREATE TABLE IF NOT EXISTS ant_hills
        (id INTEGER PRIMARY KEY NOT NULL,
        alliance TEXT,
        power INTEGER NOT NULL,
        x INTEGER NOT NULL, y INTEGER NOT NULL,
        time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (x, y))''')
      con.execute('''CREATE TABLE IF NOT EXISTS id_names
        (id INTEGER NOT NULL REFERENCES ant_hills (id) ON DELETE CASCADE ON UPDATE CASCADE,
         name TEXT NOT NULL,
         time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
         PRIMARY KEY(id, name))''')
    con.close()

  def getCon(self):
    return sqlite3.connect("./db.db")

  def addData(self, img, x, y, alliance):
    self.dataQueue.put((img, x, y, alliance))

  def start(self):
    self.stopped = False
    t = Thread(target=self.run)
    t.start()

  def stop(self):
    self.stopped = True

  def run(self):
    while not self.stopped:
      try:
        tup = self.dataQueue.get_nowait()
        self.handleText(tup)
      except Empty:
        pass
  def handleText(self, tup):
    img, x, y, alliance = tup
    img = Vision.setGrey(img)
    nameImg = Vision.crop(img, self.nameCrop)
    name = Vision.findText(nameImg)
    alliance = None
    if alliance:
      allianceImg = Vision.crop(img, self.allianceCrop)
      alliance = Vision.findText(allianceImg)

    idImg = Vision.crop(img, self.idCrop)
    uid = Vision.findText(idImg)
    powerImg = Vision.crop(img, self.powerCrop)
    power = Vision.findText(powerImg)
    power = power

    self.sendData(uid, name, alliance, power, x, y)

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

    with con:
      con.execute('''
      INSERT OR REPLACE INTO ant_hills (id, alliance, power, x, y)
      VALUES (?, ?, ?, ?, ?)
      ''',(uid, alliance, power, x, y))
      con.execute('''
      INSERT OR REPLACE INTO id_names (id, name)
      VALUES (?, ?)
      ''', (uid, name))
    con.close()