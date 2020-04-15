import cv2
import time
import math

class AnkiCar:
    
    def __init__(self, img, bounding_box, name=""):
        self.tracker = cv2.TrackerCSRT_create()
        self.tracker.init(img, tuple(bounding_box))
        self.name = name
        self.lastxPos = float(-1)
        self.lastyPos = float(-1)
        self.xPos = float(-1)
        self.yPos = float(-1)
        self.updateTime = [float(0),float(0)]
        self.unit = float(-1)
        self.laps = -1     # assuming car starts at the starting line
        self.lapStart = []     # Time when car starts a lap
        self.lapTime = []     # if not empty, show LapTime[-1]
        self.speed = []     # if not empty, show speed[-1]
        # split time cannot be defined in self class - need info from another AnkiCar
    
    def update_rect(self, img):
        self.lastxPos = self.xPos
        self.lastyPos = self.yPos
        is_success, bounding_box = self.tracker.update(img)
        if is_success:
            x, y, w, h = (int (n) for n in bounding_box)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255,0), 3)
            self.xPos = x + (w/2)
            self.yPos = y + (h/2)     # midpoint of a car 
            self.updateTime.pop()
            self.updateTime.insert(0,time.time())
            if (w > h):
                self.unit = 50/h     # in millimeters (mm)
            else:
                self.unit = 50/w

    def getLaps(self):
        if (xPos == 123 & yPos == 123):     # 123 holds the place for the position of the starting line
            self.laps = self.laps + 1
            self.lapStart.append(time.time())

    def getLapTime(self):
        if ((len(self.lapStart)) >= 2):
            startTime = self.lapStart[-2]
            endTime = self.lapStart[-1]
            oneLapTime = endTime - startTime
            self.lapTime.append(oneLapTime)

    def getSpeed(self):
        if ((self.lastxPos != float(-1)) & (self.lastyPos != float(-1)) & (self.updateTime[1] != float(0))):
            xDiff = abs(self.xPos - self.lastxPos)
            yDiff = abs(self.yPos - self.lastyPos)
            speedPerSec = (math.sqrt(math.pow(xDiff,2) + math.pow(yDiff,2)))*self.unit/(self.updateTime[0] - self.updateTime[1])
            self.speed.append(speedPerSec)


video =  cv2.VideoCapture("anki_racing_videos/anki_race1.mp4")
retval, first_frame = video.read()
bounding_boxes = cv2.selectROIs('Select Cars To Track', first_frame)
cv2.destroyWindow("Select Cars To Track")
anki_cars = [AnkiCar(first_frame, bounding_box) for bounding_box in bounding_boxes]


while True:
    retval, frame = video.read()
    if not retval:
        break
        
    for anki_car in anki_cars:
        anki_car.update_rect(frame)
        anki_car.getSpeed()
        if (len(anki_car.speed) > 0):
            print(str(anki_car.speed[-1]))
        
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) == ord("q"):
        break

video.release()
cv2.destroyAllWindows()
