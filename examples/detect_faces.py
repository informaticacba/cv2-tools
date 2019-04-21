# This test needs face_recognition library
# You can install it with: pip install face_recognition
import face_recognition
import cv2

from cv2_tools.Management import ManagerCV2
from cv2_tools.Selection import SelectorCV2
from cv2_tools.Storage import StorageCV2

def face_detector(frame, storage_cv2, scale=0.25):
    # Step 1: Prepare the frame
    small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Step 2: Create a selector
    selector = SelectorCV2(color=(200,90,0), filled=True)

    # Step 3: Get face locations and for each one add zone with tag
    face_locations = face_recognition.face_locations(rgb_small_frame)
    for i, face_location in enumerate(face_locations):
        y1, x2, y2, x1 = [position/scale for position in face_location]
        selector.add_zone((x1,y1,x2,y2), 'Face {}'.format(i))

    # Step 4: Get face landmarks and for each one add polygon
    face_landmarks_list = face_recognition.face_landmarks(frame)
    for face_landmarks in face_landmarks_list:
        for facial_feature in face_landmarks:
            selector.add_polygon(face_landmarks[facial_feature], surrounding_box=False, tags=facial_feature)

    # Step 5: Add selector to storage container, so we can save the complete process into json
    storage_cv2.add_frame(selector)

    return selector.draw(frame)


def process_video():
    manager_cv2 = ManagerCV2(cv2.VideoCapture(0), is_stream=True)
    manager_cv2.add_keystroke(27, 1, print, 'Pressed esc. Exiting', exit=True)
    storage_cv2 = StorageCV2()
    for frame in manager_cv2:
        frame = cv2.flip(frame, 1)
        frame = face_detector(frame, storage_cv2, 0.5)
        cv2.imshow('Example face_recognition', frame)
    print('FPS: {}'.format(manager_cv2.get_fps()))
    storage_cv2.save('salida.json')
    cv2.destroyAllWindows()


def load_video():
    manager_cv2 = ManagerCV2(cv2.VideoCapture(0), is_stream=True)
    manager_cv2.add_keystroke(27, 1, print, 'Pressed esc. Exiting', exit=True)
    storage_cv2 = StorageCV2(path='salida.json')

    for frame, selector in zip(manager_cv2,storage_cv2):
        frame = cv2.flip(frame, 1)
        frame = selector.draw(frame)
        cv2.imshow('Example face_recognition', frame)
    print('FPS: {}'.format(manager_cv2.get_fps()))
    cv2.destroyAllWindows()


if __name__ == '__main__':
    #process_video()
    load_video()
