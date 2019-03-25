from time import sleep
from picamera import PiCamera
import numpy as np
import cv2

with PiCamera() as camera:
    camera.resolution = (320, 240)
    camera.framerate = 24
    sleep(2)
    while (1):
        image = np.empty((240 * 320 * 3,), dtype=np.uint8)
        camera.capture(image, 'bgr')
        image = image.reshape((240, 320, 3))
        cv2.imshow('Door',image)
        k = cv2.waitKey(1)
        if k==27:    # Esc key to stop
            break
