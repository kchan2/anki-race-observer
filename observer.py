import cv2
import sys
import numpy as np
import os
import tensorflow.compat.v1 as tf
import math
import time
import json

sys.path.append("C:\\Users\\notebook\\Documents\\GitHub\\models\\research\\")
sys.path.append("C:\\Users\\notebook\\Documents\\GitHub\\models\\research\\object_detection\\utils")

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication, QListWidget, QMessageBox
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

global started
global fileCreated

started = False

global ex

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
        self.laps = float(-1)     # assuming car starts at the finish line
        self.lapCount = -1
        self.ratio = float(0)
        self.lapStart = []     # Time when car starts a lap
        self.lapTime = []     # if not empty, show LapTime[-1]
        self.speed = []     # if not empty, show speed[-1]
        # split time cannot be defined in self class - need info from another AnkiCar
    
    def update_rect(self, img):
        self.lastxPos = self.xPos
        self.lastyPos = self.yPos
        self.unit
        is_success, bounding_box = self.tracker.update(img)
        if is_success:
            x, y, w, h = (int (n) for n in bounding_box)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255,0), 3)
            self.xPos = x + (w/2)
            self.yPos = y + (h/2)     # midpoint of a car 
            self.updateTime.pop()
            self.updateTime.insert(0,time.time())
            if self.name:
                cv2.putText(img, self.name, (x,y), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0))
                

class FinishLine:

    def __init__(self, img, bounding_box):
        self.tracker = cv2.TrackerCSRT_create()
        self.tracker.init(img, tuple(bounding_box))
        self.vertical = True
        self.xPos = float(-1)
        self.yPos = float(-1)
        self.trackWidth = float(-1)
        self.unit = float(-1)

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
                self.unit = 210/w     ## in millimeters(mm)
            else:
                self.vertical = True
                self.xPos = x + (w/2)
                self.yPos = y
                self.trackWidth = h
                self.unit = 210/h     ## in millimeters(mm)

class DataHandler:

    def __init__(self, anki_cars, finishLine, list_widgets):
        self.carList = anki_cars
        self.finishLine = finishLine
        self.ranking = []
        self.currentSpeed = []
        self.avgSpeed = []
        self.laps = []
        self.currentLapTime = []
        self.avgLapTime = []
        self.splitTime = []
        self.dataBoxes = list_widgets

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

    def calculateLaps(self, anki_cars, finishLine):
        for car in anki_cars:
            car.laps = car.laps - car.ratio
            if (car.lastxPos != float(-1) and car.lastyPos != float(-1)):
                if (finishLine.vertical):
                    if (car.xPos >= finishLine.xPos and car.lastxPos < finishLine.xPos and car.yPos >= finishLine.yPos and car.yPos <= (finishLine.yPos + finishLine.trackWidth)):
                        car.lapCount = car.lapCount + 1
                        car.lapStart.append(time.time())
                        car.laps = car.lapCount
                    if (len(car.lapTime) > 0):
                        currentTime = time.time()
                        car.ratio = (currentTime - car.lapStart[-1])/car.lapTime[-1]
                        car.laps = car.lapCount + car.ratio
                        if (car.laps > (car.lapCount + 1)):
                            car.laps = float(car.lapCount + 1 - 0.000000000000001)
                else:
                    if (car.yPos >= finishLine.yPos and car.lastyPos < finishLine.yPos and car.xPos >= finishLine.xPos and car.xPos <= (finishLine.xPos + finishLine.trackWidth)):
                        car.lapCount = car.lapCount + 1
                        car.lapStart.append(time.time())
                        car.laps = car.lapCount
                    if (len(car.lapTime) > 0):
                        currentTime = time.time()
                        car.ratio = (currentTime - car.lapStart[-1])/car.lapTime[-1]
                        car.laps = car.lapCount + car.ratio

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
            self.splitTime.append(0.0)
            startIndex = 1
            lastIndex = len(anki_cars) - 1
            while (startIndex <= lastIndex):
                currentCar = anki_cars[startIndex]
                carAhead = anki_cars[startIndex-1]
                xDiff = abs(currentCar.xPos - carAhead.lastxPos)
                yDiff = abs(currentCar.yPos - carAhead.lastyPos)
                distance = float(0)
                if (currentCar.lapCount > -1 and len(carAhead.speed) > 0):
                    if (currentCar.laps <= 1):
                        if ((carAhead.laps - currentCar.laps) > 0 and len(carAhead.lapTime) > 0):
                            distance = (carAhead.lapCount - currentCar.lapCount)*(carAhead.lapTime[-1]*carAhead.speed[-1]) + (math.sqrt(math.pow(xDiff,2) + math.pow(yDiff,2)))
                        else:
                            distance = (math.sqrt(math.pow(xDiff,2) + math.pow(yDiff,2)))
                        if (currentCar.speed[-1] > 0):
                            split = distance/currentCar.speed[-1]
                            self.splitTime.append(split)
                    else:
                        split = (carAhead.laps - currentCar.laps)*(currentCar.lapTime[-1])
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
                oneAvgLapTime = float(0)
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
                laps = car.lapCount
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
        self.calculateLaps(self.carList, self.finishLine)
        self.calculateLapTime(self.carList)
        self.calculateRank(self.carList)
        self.calculateSplitTime(self.ranking)
        self.getCurrentSpeed(self.ranking)
        self.getLaps(self.ranking)
        self.getCurrentLapTime(self.ranking)

    def display(self):
        nrOfCars = len(self.ranking)
        counter = 0
        while (counter < nrOfCars):
            currentBox = self.dataBoxes[counter]
            currentBox.takeItem(0)
            currentBox.insertItem(0, "Name: " + self.ranking[counter].name)
            currentBox.item(1).setText("Ranking: " + str(counter + 1))
            currentBox.item(2).setText("Laps: " + str(self.laps[counter]))
            if (len(self.currentLapTime) > counter):
                currentBox.item(3).setText("Lap Time: " + str(self.currentLapTime[counter]))
            currentBox.item(4).setText("Speed: " + str(self.currentSpeed[counter]))
            if (len(self.splitTime) > counter):
                currentBox.item(5).setText("Split Time: " + str(self.splitTime[counter]))
            counter = counter + 1

    def fileCreate(self):
        self.calculateAvgLapTime(self.ranking)
        self.calculateAvgSpeed(self.ranking)
        data = {}
        data['anki_car'] = []
        nrOfCars = len(self.ranking)
        counter = 0
        while (counter < nrOfCars):
            data['anki_car'].append({
                'name': self.ranking[counter].name,
                'ranking': counter + 1,
                'laps': self.laps[counter],
                'avgLapTime': self.avgLapTime[counter],
                ##'fastestLapTime': '',
                'avgSpeed': self.avgSpeed[counter],
                ##'fastestSpeed': '',
                'splitTime': self.splitTime[counter]
            })
            counter = counter + 1

        fileName = time.strftime("%Y%m%d_%H_%M_%S.txt", time.localtime())
        with open(fileName, 'w') as outfile:
            json.dump(data, outfile)
##        msgBox = QMessageBox()
##        msgBox.setWindowTitle("File Create Confirmation")
##        msgBox.setText("The race data has been recorded and will be dumped into JSON format.")
##        msgBox.setInformativeText("Do you want to save the data?")
##        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
##        ret = msgBox.exec_()
##        print("Success")
##        if (ret == QMessageBox.Save):
##            print("Success")
##            self.calculateAvgLapTime(self.ranking)
##            self.calculateAvgSpeed(self.ranking)
##            data = {}
##            data['anki_car'] = []
##            nrOfCars = len(self.ranking)
##            counter = 0
##            while (counter < nrOfCars):
##                data['anki_car'].append({
##                    'name': self.ranking[counter].name,
##                    'ranking': counter + 1,
##                    'laps': self.laps[counter],
##                    'avgLapTime': self.avgLapTime[counter],
##                    ##'fastestLapTime': '',
##                    'avgSpeed': self.avgSpeed[counter],
##                    ##'fastestSpeed': '',
##                    'splitTime': self.splitTime[counter]
##                })
##                counter = counter + 1
##
##            fileName = time.strftime("%Y%m%d_%H_%M_%S.txt", time.localtime())
##            with open(fileName, 'w') as outfile:
##                json.dump(data, outfile)
##            print("Success")
        

PATH_TO_LABELS = r'C:\Users\notebook\Documents\GitHub\anki-race-observer\training\label_map.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

MODEL_NAME = 'inference_graph'
PATH_TO_FROZEN_GRAPH = r'C:\Users\notebook\Documents\GitHub\anki-race-observer\training\frozen_inference_graph.pb'
TEST_IMAGE_DIR_PATH = r"C:\Users\notebook\Documents\GitHub\anki-race-observer\images"

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')


category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)


def run_inference_for_single_image(image, graph, tensor_dict):
    if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(
            tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [
                                   real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [
                                   real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[0], image.shape[1])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.5), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
    image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

    # Run inference
    sess = tf.Session()
    output_dict = sess.run(tensor_dict,
                           feed_dict={image_tensor: np.expand_dims(image, 0)})

    # all outputs are float32 numpy arrays, so convert types as appropriate
    output_dict['num_detections'] = int(output_dict['num_detections'][0])
    output_dict['detection_classes'] = output_dict[
        'detection_classes'][0].astype(np.uint8)
    output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
    output_dict['detection_scores'] = output_dict['detection_scores'][0]
    if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict

class Thread(QThread):

    global started
    global fileCreated
    global ex
    
    changePixmap = pyqtSignal(QImage)

    def __init__(self, list_widgets, parent=None):
        QThread.__init__(self, parent=parent)
        self.list_widgets = list_widgets
        self.filepath = None
        
    def run(self):
        global started
        global fileCreated
        
        video = cv2.VideoCapture(self.filepath)
        ret, frame = video.read()
        finishLine = None
        anki_cars = []

        with detection_graph.as_default():
            with tf.Session() as sess:
                # Get handles to input and output tensors
                ops = tf.get_default_graph().get_operations()
                all_tensor_names = {output.name for op in ops for output in op.outputs}
                tensor_dict = {}
                for key in [
                    'num_detections', 'detection_boxes', 'detection_scores',
                    'detection_classes', 'detection_masks'
                ]:
                    tensor_name = key + ':0'
                    if tensor_name in all_tensor_names:
                        tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                            tensor_name)

                
                frame
                frame_height, frame_width, channels  = frame.shape
                # Actual detection.
                output_dict = run_inference_for_single_image(
                    frame, detection_graph, tensor_dict)
                boxes = output_dict['detection_boxes']
                # get all boxes from an array
                max_boxes_to_draw = boxes.shape[0]
                # get scores to get a threshold
                scores = output_dict['detection_scores']
                # this is set as a default for now
                min_score_thresh=.5
                # iterate through all boxes detected (there are alot of detection boxes most are not the ones we want)
                for i in range(min(max_boxes_to_draw, boxes.shape[0])):
                    # box is not none and score is higher than 50% (these are the detections we want)
                    if scores is None or scores[i] > min_score_thresh:
                        # boxes[i] is the box which will be drawn
                        class_name = category_index[output_dict['detection_classes'][i]]['name']
                        # boxes[i] holds [ymin, xmin, ymax, ymin] they are floats ranging from 0 to 1 
                        y1,x1,y2,x2 = boxes[i]
                        coordinates = (x1*frame_width, y1*frame_height, x2*frame_width, y2*frame_height)
                        coordinates = tuple((int (n) for n in coordinates))
                        if class_name == "Finish Line":
                            finish_line_coordinates = coordinates
                            fl_x1, fl_y1, fl_x2, fl_y2 = finish_line_coordinates
                            fl_w = fl_x2-fl_x1
                            fl_h = fl_y2-fl_y1
                            finishLine = FinishLine(frame, (fl_x1,fl_y1,fl_w,fl_h))
                            finishLine.update_rect(frame)
                        else:
                            x1,y1,x2,y2 = coordinates
                            w = x2-x1
                            h = y2-y1
                            anki_cars.append(AnkiCar(frame, (x1,y1,w,h), class_name))

        
        dataHandler = DataHandler(anki_cars, finishLine, self.list_widgets)
        
        for anki_car in anki_cars:
            anki_car.unit = finishLine.unit

        fileCreated = False

        while True:
            ret, frame = video.read()
            if ret:
                if not started:
                    dataHandler.fileCreate()
                    fileCreated = True
                    self.quit()
                    break
                for anki_car in anki_cars:
                    anki_car.update_rect(frame)
                dataHandler.handle()
                dataHandler.display()
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)
            else:
                break
        if not fileCreated:
            dataHandler.fileCreate()
            fileCreated = True
            ex.fileCreate()
            self.quit()
##        else:
##            print("Success")
##            msgBox2 = QMessageBox()
##            print("Success")
##            msgBox2.setWindowTitle("File Create Confirmation")
##            print("Success")
##            msgBox2.setText("The data has been saved.")
##            print("Success")
##            msgBox2.setStandardButtons(QMessageBox.Ok)
##            print("Success")
##            ret2 = msgBox2.exec_()
##            print("Success")
##            if (ret2 == QMessageBox.Ok):
##                print("Success")
##                print()
            

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))
        self.label.setScaledContents(True)

    def initUI(self):
        self.setWindowTitle("ANKI Race Observer")
        self.setObjectName("MainWindow")
        sizeObject = QtWidgets.QDesktopWidget().screenGeometry(0)
        self.resize(sizeObject.width()-20, sizeObject.height()-100)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)

        self.listWidget_1 = QListWidget(self.centralwidget)
        self.listWidget_1.setObjectName("listWidget_1")
        name1 = "Name: "
        ranking1 = "Ranking: "
        laps1 = "Laps: "
        lapTime1 = "Lap Time: "
        speed1 = "Speed: "
        split1 = "Split Time: "
        self.listWidget_1.addItem(name1)
        self.listWidget_1.addItem(ranking1)
        self.listWidget_1.addItem(laps1)
        self.listWidget_1.addItem(lapTime1)
        self.listWidget_1.addItem(speed1)
        self.listWidget_1.addItem(split1)
        self.horizontalLayout_2.addWidget(self.listWidget_1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)

        self.listWidget_2 = QListWidget(self.centralwidget)
        self.listWidget_2.setObjectName("listWidget_2")
        name2 = "Name: "
        ranking2 = "Ranking: "
        laps2 = "Laps: "
        lapTime2 = "Lap Time: "
        speed2 = "Speed: "
        split2 = "Split Time: "
        self.listWidget_2.addItem(name2)
        self.listWidget_2.addItem(ranking2)
        self.listWidget_2.addItem(laps2)
        self.listWidget_2.addItem(lapTime2)
        self.listWidget_2.addItem(speed2)
        self.listWidget_2.addItem(split2)
        self.horizontalLayout_2.addWidget(self.listWidget_2)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)

        self.listWidget_3 = QListWidget(self.centralwidget)
        self.listWidget_3.setObjectName("listWidget_3")
        name3 = "Name: "
        ranking3 = "Ranking: "
        laps3 = "Laps: "
        lapTime3 = "Lap Time: "
        speed3 = "Speed: "
        split3 = "Split Time: "
        self.listWidget_3.addItem(name3)
        self.listWidget_3.addItem(ranking3)
        self.listWidget_3.addItem(laps3)
        self.listWidget_3.addItem(lapTime3)
        self.listWidget_3.addItem(speed3)
        self.listWidget_3.addItem(split3)
        self.horizontalLayout_2.addWidget(self.listWidget_3)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)

        self.listWidget_4 = QListWidget(self.centralwidget)
        self.listWidget_4.setObjectName("listWidget_4")
        name4 = "Name: "
        ranking4 = "Ranking: "
        laps4 = "Laps: "
        lapTime4 = "Lap Time: "
        speed4 = "Speed: "
        split4 = "Split Time: "
        self.listWidget_4.addItem(name4)
        self.listWidget_4.addItem(ranking4)
        self.listWidget_4.addItem(laps4)
        self.listWidget_4.addItem(lapTime4)
        self.listWidget_4.addItem(speed4)
        self.listWidget_4.addItem(split4)
        self.horizontalLayout_2.addWidget(self.listWidget_4)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)

        self.listWidget_5 = QListWidget(self.centralwidget)
        self.listWidget_5.setObjectName("listWidget_5")
        name5 = "Name: "
        ranking5 = "Ranking: "
        laps5 = "Laps: "
        lapTime5 = "Lap Time: "
        speed5 = "Speed: "
        split5 = "Split Time: "
        self.listWidget_5.addItem(name5)
        self.listWidget_5.addItem(ranking5)
        self.listWidget_5.addItem(laps5)
        self.listWidget_5.addItem(lapTime5)
        self.listWidget_5.addItem(speed5)
        self.listWidget_5.addItem(split5)
        self.horizontalLayout_2.addWidget(self.listWidget_5)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem5)

        self.list_widgets = [self.listWidget_1, self.listWidget_2, self.listWidget_3, self.listWidget_4, self.listWidget_5]

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout_3.addItem(spacerItem6)
        self.label = QtWidgets.QLabel('Waiting for video input...')
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        spacerItem7 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout_3.addItem(spacerItem7)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalFrame = QtWidgets.QFrame(self.centralwidget)
        self.horizontalFrame.setObjectName("horizontalFrame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton = QtWidgets.QPushButton("Start")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMaximumSize(QtCore.QSize(16777215, 50))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("C:/Users/BuzzPics/icons/play-circle.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("C:/Users/BuzzPics/icons/stop-circle.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pushButton.setIcon(icon)
        self.pushButton.setAutoDefault(False)
        self.pushButton.setFlat(False)
        self.pushButton.clicked.connect(self.displayFrame)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addWidget(self.horizontalFrame)
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.t = Thread(self.list_widgets, parent=None)
        self.t.changePixmap.connect(self.setImage)
        
        self.show()

    def displayFrame(self):
        global started

        if (started):
            self.fileCreate()
        else:
            text, ok = QtWidgets.QInputDialog.getText(self, 'File Path', 'Enter the path to the video file:')
            if ok and text:
                self.t.filepath = str(text)
            self.t.start()
            self.pushButton.setFlat(False)
            self.pushButton.setText("Stop")
            started = True
        
    def fileCreate(self):
        global started
        self.pushButton.setFlat(False)
        self.pushButton.setText("Start")
        started = False

if __name__ == '__main__':
    global ex
    
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
