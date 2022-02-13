import cv2 as cv
import numpy as np
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract'

class Vision:
    # given a list of [x, y, w, h] rectangles returned by find(), convert those into a list of
    # [x, y] positions in the center of those rectangles where we can click on those found items
    @staticmethod
    def getClickPoints(rectangles) -> list[tuple[int, int]]:
        points = []
        if rectangles is None:
            rectangles = []
        # Loop over all the rectangles
        for rect in rectangles:

            points.append(Vision.getClickPoint(rect))

        return points

    @staticmethod
    def getClickPoint(rect: tuple[int, int, int, int], offset: tuple[int, int, int, int] = None) -> tuple[int, int]:
        (x, y, w, h) = rect

        point = (x + int(w/2), y + int(h/2))
        if offset is not None:
            point[0] += offset[0]
            point[1] += offset[1]
        return point

    # given a list of [x, y, w, h] rectangles and a canvas ima~~ge to draw on, return an image with
    # all of those rectangles drawn
    @staticmethod
    def drawRectangles(baseImg, rectangles):
        # these colors are actually BGR
        line_color = (0, 255, 0)
        line_type = cv.LINE_4

        for (x, y, w, h) in rectangles:
            # determine the box positions
            top_left = (x, y)
            bottom_right = (x + w, y + h)
            # draw the box
            cv.rectangle(baseImg, top_left, bottom_right, line_color, lineType=line_type)
        return baseImg

    @staticmethod
    def drawCoordinates(baseImg, coords, names):
        line_color = (0,255,255)
        line_type = cv.LINE_4
        i = 0
        for (x1, y1, x2, y2) in coords:
            cv.rectangle(baseImg, (x1, y1), (x2, y2), line_color, lineType=line_type)
            cv.putText(baseImg, str(names[i]), (x1, y1), cv.FONT_HERSHEY_PLAIN, 1.5, line_color, lineType=line_type)
            i += 1
        return baseImg

    # given a list of [x, y] positions and a canvas image to draw on, return an image with all
    # of those click points drawn on as crosshairs
    @staticmethod
    def drawCrosshairs(baseImg, points):
        # these colors are actually BGR
        marker_color = (255, 0, 255)
        marker_type = cv.MARKER_CROSS

        for (center_x, center_y) in points:
            # draw the center point
            cv.drawMarker(baseImg, (center_x, center_y), marker_color, marker_type)

        return baseImg

    @staticmethod
    def find(baseImg, searchImg, threshold=0.5, method=cv.TM_CCOEFF_NORMED):
        result = cv.matchTemplate(baseImg, searchImg, method)
        matches = Vision.getMatches(result, (searchImg.shape[1], searchImg.shape[0]), threshold)
        return matches

    @staticmethod
    def getMatches(results, size, threshold=0.5):
        locations = np.where(results >= threshold)
        locations = list(zip(*locations[::-1]))
        rectangles = []
        for loc in locations:
            rect = [int(loc[0]), int(loc[1]), size[0], size[1]]
            rectangles.append(rect)
            rectangles.append(rect)
        rectangles, _weights = cv.groupRectangles(rectangles, groupThreshold=1, eps=0.5)
        return rectangles

    @staticmethod
    def findText(img):
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        return pytesseract.image_to_string(img).strip()

    @staticmethod
    def setGrey(img):
        return cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    @staticmethod
    def crop(img, points):
        return img[points[1]:points[3],points[0]:points[2]]
