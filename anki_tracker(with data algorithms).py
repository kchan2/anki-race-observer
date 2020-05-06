import cv2
import time
import math
import json

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
        self.laps = float(-1)     # assuming car starts at the starting line
        self.lapCount = -1
        self.ratio = float(0)
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


class StartingLine:

    def __init__(self, img, bounding_box):
        self.tracker = cv2.TrackerCSRT_create()
        self.tracker.init(img, tuple(bounding_box))
        self.vertical = True
        self.xPos = float(-1)
        self.yPos = float(-1)
        self.trackWidth = float(-1)

    def update_rect(self, img):
        is_success, bounding_box = self.tracker.update(img)
        if is_success:
            x, y, w, h = (int (n) for n in bounding_box)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255,0), 3)
            if (w > h):
                self.vertical = False
                self.yPos = y + (h/2)
                self.xPos = x
                self.trackWidth = w
            else:
                self.vertical = True
                self.xPos = x + (w/2)
                self.yPos = y
                self.trackWidth = h


class DataHandler:

    def __init__(self, anki_cars, startingLine):
        self.carList = anki_cars
        self.startingLine = startingLine
        self.ranking = []
        self.currentSpeed = []
        self.avgSpeed = []
        self.laps = []
        self.currentLapTime = []
        self.avgLapTime = []
        self.splitTime = []

    def calculateRank(self, anki_cars):
        if (len(anki_cars[0].speed) > 0):
            cars = anki_cars
            sortSpeed = sorted(cars, key = lambda x : x.speed[-1], reverse = True)
            self.ranking = sorted(sortSpeed, key = lambda x : x.laps, reverse = True)

    def calculateSpeed(self, anki_cars):
        for car in anki_cars:
            if ((car.lastxPos != float(-1)) and (car.lastyPos != float(-1)) & (car.updateTime[1] != float(0))):
                xDiff = abs(car.xPos - car.lastxPos)
                yDiff = abs(car.yPos - car.lastyPos)
                speedPerSec = (math.sqrt(math.pow(xDiff,2) + math.pow(yDiff,2)))*car.unit/(car.updateTime[0] - car.updateTime[1])
                car.speed.append(speedPerSec)

    def calculateLaps(self, anki_cars, startingLine):
        for car in anki_cars:
            car.laps = car.laps - car.ratio
            if (car.lastxPos != float(-1) and car.lastyPos != float(-1)):
                if (startingLine.vertical):
                    if (car.xPos >= startingLine.xPos and car.lastxPos < startingLine.xPos and car.yPos >= startingLine.yPos and car.yPos <= (startingLine.yPos + startingLine.trackWidth)):
                        car.lapCount = car.lapCount + 1
                        car.lapStart.append(time.time())
                        car.laps = car.lapCount
                    if (len(car.lapTime) > 0):
                        currentTime = time.time()
                        car.ratio = (currentTime - car.lapStart[-1])/car.lapTime[-1]
                        car.laps = car.lapCount + car.ratio
##                        if (car.laps > (car.lapCount + 1)):
##                            car.laps = float(car.lapCount + 1 - 0.000000000001)
                else:
                    if (car.yPos >= startingLine.yPos and car.lastyPos < startingLine.yPos and car.xPos >= startingLine.xPos and car.xPos <= (startingLine.xPos + startingLine.trackWidth)):
                        car.lapCount = car.lapCount + 1
                        car.lapStart.append(time.time())
                        car.laps = car.lapCount
                    if (len(car.lapTime) > 0):
                        currentTime = time.time()
                        car.ratio = (currentTime - car.lapStart[-1])/car.lapTime[-1]
                        car.laps = car.lapCount + car.ratio
##                        if (car.laps > (car.lapCount + 1)):
##                            car.laps = float(car.lapCount + 1 - 0.000000000001)

    def calculateLapTime(self, anki_cars):
        for car in anki_cars:
            if ((len(car.lapStart)) >= 2):
                startTime = car.lapStart[-2]
                endTime = car.lapStart[-1]
                oneLapTime = endTime - startTime
                car.lapTime.append(oneLapTime)

    def calculateSplitTime(self, anki_cars):
        if (len(anki_cars) >= 2):
            self.splitTime = []
            startIndex = 1
            lastIndex = len(anki_cars) - 1
            while (startIndex <= lastIndex):
                currentCar = anki_cars[startIndex]
                carAhead = anki_cars[startIndex-1]
                xDiff = abs(currentCar.xPos - carAhead.lastxPos)
                yDiff = abs(currentCar.yPos - carAhead.lastyPos)
                distance = float(0)
                if (len(carAhead.speed) > 0):
                    if ((carAhead.laps - currentCar.laps) > 0 and len(carAhead.lapTime) > 0):
                        distance = (carAhead.laps - currentCar.laps)*(carAhead.lapTime[-1]*carAhead.speed[-1]) + (math.sqrt(math.pow(xDiff,2) + math.pow(yDiff,2)))
                    else:
                        distance = (math.sqrt(math.pow(xDiff,2) + math.pow(yDiff,2)))
                    split = distance/currentCar.speed[-1]
                    self.splitTime.append(split)
                    startIndex = startIndex + 1
    
    def calculateAvgSpeed(self, rank):
        if (len(rank) > 0):
            for car in rank:
                totalSpeed = float(0)
                oneAvgSpeed = float(1)
                for s in car.speed:
                    totalSpeed = totalSpeed + s
                if (len(car.speed) > 0):
                    oneAvgSpeed = totalSpeed/len(car.speed)
                self.avgSpeed.append(oneAvgSpeed)

    def calculateAvgLapTime(self, rank):
        if (len(rank) > 0):
            for car in rank:
                totalLapTime = float(0)
                oneAvgLapTime = float(1)
                for l in car.lapTime:
                    totalLapTime = totalLapTime + l
                if (len(car.lapTime) > 0):
                    oneAvgLapTime = totalLapTime/len(car.lapTime)
                self.avgLapTime.append(oneAvgLapTime)

    def getCurrentSpeed(self, rank):
        current = []
        if (len(rank) > 0):
            for car in rank:
                speed = car.speed[-1]
                current.append(speed)
            self.currentSpeed = current

    def getLaps(self, rank):
        current = []
        if (len(rank) > 0):
            for car in rank:
                laps = car.laps
                current.append(laps)
            self.laps = current

    def getCurrentLapTime(self, rank):
        current = []
        if (len(rank) > 0):
            for car in rank:
                if (len(car.lapTime) > 0):
                    lapTime = car.lapTime[-1]
                    current.append(lapTime)
                self.currentLapTime = current
    
    def handle(self):
        self.calculateSpeed(self.carList)
        self.calculateLaps(self.carList, self.startingLine)
        self.calculateLapTime(self.carList)
        self.calculateRank(self.carList)
        self.calculateSplitTime(self.ranking)
        self.getCurrentSpeed(self.ranking)
        self.getLaps(self.ranking)
        self.getCurrentLapTime(self.ranking)

    def display(self):
##        print(self.ranking)
        print("Current speed: " + str(self.currentSpeed))
        print("Completed laps: " + str(self.laps))
        print("Current lap time: " + str(self.currentLapTime))
        print("Split time: " + str(self.splitTime))
        print("")
        

video =  cv2.VideoCapture("anki_racing_videos/anki_race1.mp4")
retval, first_frame = video.read()
bounding_boxes = cv2.selectROIs('Select Cars To Track', first_frame)
cv2.destroyWindow("Select Cars To Track")
anki_cars = []
for bounding_box in bounding_boxes:
    if (((bounding_box[2]/bounding_box[3]) > 5) or ((bounding_box[3]/bounding_box[2]) > 5)):
        startingLine = StartingLine(first_frame, bounding_box)
    else: anki_cars.append(AnkiCar(first_frame, bounding_box))
dataHandler = DataHandler(anki_cars, startingLine)


while True:
    retval, frame = video.read()
    if not retval:
        break
        
    startingLine.update_rect(frame)
    for anki_car in anki_cars:
        anki_car.update_rect(frame)
    dataHandler.handle()
    dataHandler.display()
    
        
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) == ord("q"):
        break

video.release()
cv2.destroyAllWindows()

dataHandler.calculateAvgLapTime(dataHandler.ranking)
dataHandler.calculateAvgSpeed(dataHandler.ranking)
print("Average Lap Time: " + str(dataHandler.avgLapTime))
print("Average Speed: " + str(dataHandler.avgSpeed))
print("")

##data = {}
##
##for car in dataHandler.ranking:
##    data['anki_car'] = []
##    data['anki_car'].append({
##        'name': '',
##        'ranking': '',
##        'laps': '',
##        'avgLapTime': '',
##        'fastestLapTime': '',
##        'avgSpeed': '',
##        'fastestSpeed': '',
##        'splitTime': '',
##    })
##
##with open('data.txt', 'w') as outfile:
##    json.dump(data, outfile)
##
