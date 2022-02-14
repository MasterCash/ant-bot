# ant-bot
ants go marching...

# Overview
This is a bot to map out the users across the map of an The Ants: underground Kingdom mobile game.

This bot works with BlueStacks in order to send inputs and record data using Computer vision into a SQLite database.

# Setup
## Requirement:

* Python 3.10
  * pywin32
  * pytesseract
  * opencv-python
  * sqlite-python
  * numpy
  * pygetwindow
* tesseract
* BlueStacks 5


## BlueStacks
This bot uses special game control points on the bluestacks to make it easier to interact with the game.

Keys:
* Tab: hovering over the search icon on the map
* X: hovering over the X coordinate field on the search coordinate tab
* Y: hovering over the Y coordinate field on the search coordinate tab
* F: hovering over the coordinate search icon on the search coordinate tab
* Space: hovering over the Search Coordinate Tab Icon in the Search Window

In Addition: the program will automatically resize any windows to match a 575x1000 window size as this is what the screenshots were taken from.

If you wish to change this, new screenshots would need to be taken and new bounding boxes would need to be positioned.
You can use the `setup.py` script to find new box locations for new icons.

## setup.py
This handy script was built to help isolate locations of where to look for icons to speed up searching by shrinking the search image for each icon.
It provides sliders to move around points to highlight areas.

Commenting out `iconCrops = Consts.iconCrops.copy()` line from `setup.py` will allow you to check the text scraper boxes to find the right adjustments.

usage: `python setup.py <window name>`

\<window name>: if no window name is provided, "BlueStacks" will be used by default

Keys:
* Q: will quit setup.py
* C: will take a screenshot of the cropped image and save it as {icon.name}-icon.png in greyscale

After quitting the program, the selected values found during testing will be outputted to the console for copying into the corresponding script locations.


## main.py
Currently, the main script is setup to look for 4 windows named: "BlueStacks", "BlueStacks 1", "BlueStacks 2", "BlueStacks 3"

if you wish to add more or if you changed the name of your BlueStack's instance, you will need to update this list to reflect those changes. Any window not found will not be used in running.

# Usage

to run: `