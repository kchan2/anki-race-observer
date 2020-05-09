# Anki Race Observer

Anki Race Observer is a tool used to track Anki cars and obtain racing statistics from a race using computer vision.
  Given a video stream of an Anki race, the observer will detect each Anki car and will update their stats on-screen as the video stream continues. Once the stream ends, it presents the option to export the stats of the race in a .json file.

It is written in Python and uses Tensorflow for detection, OpenCV for image processing, and PyQt for its graphical user interface. 

![demo of program running](./demo/demo1.png)

![demo2 of program running](./demo/demo2.png)

### Installation
To run Anki Race Observer, you need to have Python 3.7. (Versions such as 3.7.6, 3.7.7, etc. work as well)

To install, visit the official website for [the latest version](https://www.python.org/downloads/release/python-377/) (link leads to 3.7.7, but all 3.7 releases should work) and download the 64 bit installer for Windows or Mac respectively.

Anki Race Observer requires the following dependencies to run:

  - Tensorflow Object Detection API
  - OpenCV
  - PyQt5
  
To install the Tensorflow Object Detection API follow the [installation documentation.](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md)

Install OpenCV using the following command:

```sh
$ pip install opencv-contrib-python
```

Install PYQt5 using the following command:

```sh
$ pip install PyQt5
```

### How to Run the Program
After installing all required dependencies, clone anki-race-observer-master or download the master branch as a zip folder.

To run the ANKI Race Observer, you have to change a few lines in observer.py for the program to run:

Line 10: 
```sh
sys.path.append("<YOUR PATH TO THE MODELS FOLDER YOU DOWNLOAD WHILE INSTALLING TENSORFLOW>\\models\\research\\")
```
Line 11:
```sh
sys.path.append("<YOUR PATH TO THE MODELS FOLDER YOU DOWNLOAD WHILE INSTALLING TENSORFLOW >\\models\\research\\object_detection\\utils")
```
Line 331:
```sh
PATH_TO_LABELS = r'<YOUR PATH TO THE anki-race-observer-master BRANCH YOU CLONED/DOWNLOADED>\anki-race-observer\training\label_map.pbtxt'
```
Line 335:
```sh
PATH_TO_FROZEN_GRAPH = r'<YOUR PATH TO THE anki-race-observer-master BRANCH YOU CLONED/DOWNLOADED>\anki-race-observer\training\frozen_inference_graph.pb'
```
Line 336:
```sh
TEST_IMAGE_DIR_PATH = r"<YOUR PATH TO THE anki-race-observer-master BRANCH YOU CLONED/DOWNLOADED>\anki-race-observer\images"
```

After changing these lines, the program should now be runnable.

To start a race, click the “Start” button. An input dialog window should pop up, prompting for a file path. You can use the test videos that are already in the repository by typing anki_racing_videos\<filename>, or you can use your own ANKI racing videos if you have them. If an error occurs, a message box should pop up describing the error. Else, wait a few seconds for the cars to be detected and enjoy the race!

To stop a race, click the “Stop” button. It should be the same button that you clicked to start the race. A message box should pop up, asking if you want the data to be save or not. Choose “Save” if you want to save the data, then a file in JSON format will be generated in the folder where the observer.py file is located, containing all the data from the race.
When you are done with the observer, just exit the window, and the program will be terminated.

**ATTENTION**
Do NOT click on any of the message boxes! It will cause the program to crash. To choose a button, use TAB and ENTER on keyboard instead. If the program crashes when a message box pops up, please do not panic – just close the python shell so that the program can be terminated, then start it over. 

If you have any questions/concerns regarding to ANKI Race Observer, please contact the development team at kchan2@oswego.edu .


