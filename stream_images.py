import picamera
import cv2
import time
import numpy as np

with picamera.PiCamera() as camera:
    camera.resolution = (1280, 720)
    time.sleep(2)
    while(1):
        image = np.empty((720*1280*3), dtype=np.uint8)
        camera.capture(image, 'bgr')
        image = image.reshape((720, 1280, 3))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = image[230:470,550:790]
        cv2.imshow('Preview', image)
        cv2.waitKey(100)
