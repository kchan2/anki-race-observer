
import numpy as np
import os
import sys
import tensorflow as tf
import cv2

from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util


class AnkiCar:
    def __init__(self, img, bounding_box, name=""):
        self.tracker = cv2.TrackerCSRT_create()
        self.tracker.init(img, tuple(bounding_box))
        self.name = name

    
    def update_rect(self, img):
        is_tracked, bounding_box = self.tracker.update(img)
        if is_tracked:
            x, y, w, h = (int (n) for n in bounding_box)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
            if self.name:
                cv2.putText(img, self.name, (x,y), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0))



PATH_TO_LABELS = r'C:\Users\Jerem\tensorflow\models\research\object_detection\training\label_map.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

MODEL_NAME = 'inference_graph'
PATH_TO_FROZEN_GRAPH = r'C:\Users\Jerem\tensorflow\models\research\object_detection\inference_graph\frozen_inference_graph.pb'
TEST_IMAGE_DIR_PATH = r"C:\Users\Jerem\OneDrive\Documents\CourseWork\CSC380\TestImages"


detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')


category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)


def run_inference_for_single_image(image, graph):
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


video =  cv2.VideoCapture("videos/test1.mp4")
retval, first_frame = video.read()

finish_line_coordinates = None
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

        
        first_frame
        frame_height, frame_width, channels  = first_frame.shape

        # Actual detection.
        output_dict = run_inference_for_single_image(
            first_frame, detection_graph)

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
                else:
                    x1,y1,x2,y2 = coordinates
                    w = x2-x1
                    h = y2-y1
                    anki_cars.append(AnkiCar(first_frame, (x1,y1,w,h), class_name))
    

fl_x1, fl_y1, fl_x2, fl_y2 = finish_line_coordinates

while True:
    retval, frame = video.read()    
    if not retval:
        break

    for anki_car in anki_cars:
        anki_car.update_rect(frame)

    # drawing rectangle on the finish line 
    cv2.rectangle(frame, (fl_x1, fl_y1), (fl_x2, fl_y2), (0,255,0), 2)

    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) == ord("q"):
        break

video.release()
cv2.destroyAllWindows()