import cv2


class AnkiCar:
    
    def __init__(self, img, bounding_box, name=""):
        self.tracker = cv2.TrackerCSRT_create()
        self.tracker.init(img, tuple(bounding_box))
        self.name = name
    
    def update_rect(self, img):
        is_success, bounding_box = self.tracker.update(img)
        if is_success:
            x, y, w, h = (int (n) for n in bounding_box)
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255,0), 3)


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
        
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) == ord("q"):
        break

video.release()
cv2.destroyAllWindows()