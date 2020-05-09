# Anki Race Observer

Anki Race Observer is a tool used to track Anki cars and obtain racing statistics from a race using computer vision.
  Given a video stream of an Anki race, the observer will detect each Anki car and will update their stats on-screen as the video stream continues. Once the stream ends, it presents the option to export the stats of the race in a .json file.

It is written in Python and uses Tensorflow for detection, OpenCV for image processing, and PyQt for its graphical user interface. 

![demo of program running](./demo/demo1.png)

![demo2 of program running](./demo/demo2.png)

### Installation

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
