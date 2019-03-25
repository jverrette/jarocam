import picamera
import cv2
import numpy as np
import time

def capture(camera):
    image = np.empty((720*1280*3), dtype=np.uint8)
    camera.capture(image, 'bgr')
    image = image.reshape((720, 1280, 3))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = image[230:470,550:790]
    return image

with picamera.PiCamera() as camera:
    camera.resolution = (1280,720)
    time.sleep(2)
    for exp in ['auto']:#, 'snow', 'backlight', 'spotlight', 'snow', 'beach', 'verylong', 'fixedfps']:
        camera.exposure_mode = exp
        image = capture(camera)
        window_name = camera.exposure_mode
        print(window_name)
        mask = np.zeros([240,240], dtype=np.uint8)
        cv2.circle(mask, (130,130), 120, 255, -1)
        #cv2.rectangle(mask, (75,90), (130,150), 0, -1)
        cv2.rectangle(mask, (160,100), (239,239), 0, -1)
        cv2.rectangle(mask, (0,200), (239,239), 0, -1)
        cv2.rectangle(mask, (0,100), (30,239), 0, -1)
        print('intensity='+str(cv2.mean(image, mask=mask)[0]))
        cv2.rectangle(image, (80,120), (140,165), 255, 1)
        image = cv2.bitwise_and(image, image, mask=mask)
        cv2.imshow(window_name, image)
    cv2.waitKey(0)
