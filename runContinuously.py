#!/usr/bin/python

# TODO
# X back to first bright frame for ref
# X adjust light threshold
# X tune blob size
# X Draw bbox, centroid, and timestamp on light videos
# - get new gmail account and implement google drive backup of videos and midnight deletion

import time
import picamera
import imageio
import cv2
import datetime
import numpy as np
import os
import smtplib
import logging
import sys
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.encoders import encode_base64

class MotionTracker():
    def __init__(self):
        self.reset()
        self.mask = np.zeros([240, 240], dtype=np.uint8)
        cv2.circle(self.mask, (130,130), 120, 255, -1) # former center (120,120)
        cv2.rectangle(self.mask, (160,100), (239,239), 0, -1)
        cv2.rectangle(self.mask, (0,200), (239,239), 0, -1)
        cv2.rectangle(self.mask, (0,100), (30,239), 0, -1)

    def framesSinceLastMotion(self):
        return self.count_since_last_motion

    def checkForMotion(self, image):
        annotation = {'blob_size':None, 'top_left':None, 'bot_right':None, 'centroid':None}
        self.motion_frames.append(image)
        image = cv2.GaussianBlur(image, (21,21), 0)
        image = cv2.bitwise_and(image, image, mask=self.mask)

        if self.first_frame is None:
            nower = datetime.datetime.now()
            self.timestamp= str(nower.hour)+'-'+str(nower.minute)
            self.first_frame = image
            return False, annotation
        
        binary = cv2.threshold(cv2.absdiff(self.first_frame, image), 25, 255, cv2.THRESH_BINARY)[1]
        binary = cv2.dilate(binary, None, iterations=2)
        (cnts, _) = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
        maxer = 0
        indexer = -1
        rect = None
        for i, c in enumerate(cnts):
            area = cv2.contourArea(c)
            if area > maxer:
                indexer = i
                maxer = area
                rect = cv2.boundingRect(c)
        if maxer > 300:
            contour = cnts[indexer]
            M = cv2.moments(contour)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            self.centroids.append((cx,cy))
            self.count_since_last_motion = 0
            annotation['blob_size'] = maxer
            annotation['centroid'] = (cx,cy)
            annotation['top_left'] = (rect[0], rect[1])
            annotation['bot_right'] = (rect[0]+rect[2], rect[1]+rect[3])
            return True, annotation
        else:
            self.count_since_last_motion = self.count_since_last_motion + 1
            return False, annotation

    def saveMotion(self, prefix):
        images = []
        for f in self.motion_frames:
            images.append(f)
        nower = datetime.datetime.now()
        if self.timestamp is None:
            self.timestamp= str(nower.hour)+'-'+str(nower.minute)
        datestr = str(nower.year)+'-'+str(nower.month)+'-'+str(nower.day)
        checkAndCreateDirectory(datestr)
        outfile = os.path.join('/home/teamjjj/Videos',datestr,prefix,prefix+self.timestamp+'.mp4')
        imageio.mimsave(outfile, images, fps=5)
        return outfile       

    def reset(self):
        self.first_frame = None      
        self.resetMotionFrames()

    def resetMotionFrames(self):
        self.count_since_last_motion = 0
        self.motion_frames = []
        self.centroids = []
        self.timestamp = None

    def correctNeighbors(self):
        within_box = np.zeros(len(self.centroids), dtype=np.float)
        for i, (cx,cy) in enumerate(self.centroids):
            # if cx > 75 and cx < 145 and cy > 110 and cy < 155:
            if cx > 80 and cx < 140 and cy > 120 and cy < 165:
                within_box[i] = 1
        is_it_them = np.mean(within_box)
        if is_it_them > 0.9:
            return True
        else:
            return False

class LightRecorder():
    def __init__(self):
        self.reset()
    
    def addImage(self, image, annotation):
        image = self.addAnnotation(image, annotation)
        self.frame_buffer.append(image) 
        if len(self.frame_buffer) > 200: # Approx 2 min of wall time
            self.saveVideo()
            self.frame_buffer = []
            self.video_index = self.video_index + 1

    def addAnnotation(self, image, annotation):
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR )
        #cv2.rectangle(image, (75,110), (135,155), (255,0,0),1) 
        cv2.rectangle(image, (80,120), (140,165), (255,0,0),1) 
        if annotation['blob_size'] is not None:
            # Rectangle for detected motion
            cv2.rectangle(image, annotation['top_left'], annotation['bot_right'], (0,255,0), 1)        
            # Centroid
            cv2.circle(image, annotation['centroid'], 3, 0, -1) 
            # Blob size
            cv2.putText(image, "Blob Area: "+str(annotation['blob_size']), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1) 
        cv2.putText(image, datetime.datetime.now().strftime("%A %d %B %Y %H:%M:%S"),(10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1) 
        return image        

    def saveVideo(self):
        images = []
        for f in self.frame_buffer:
            images.append(f)
        if len(images) > 2:
            nower = datetime.datetime.now()
            if self.timestamp is None:
                self.timestamp= str(nower.hour)+'-'+str(nower.minute)
            datestr = str(nower.year)+'-'+str(nower.month)+'-'+str(nower.day)
            checkAndCreateDirectory(datestr)
            outfile = os.path.join('/home/teamjjj/Videos',datestr,'light','light'+self.timestamp+'_part'+str(self.video_index)+'.mp4')
            imageio.mimsave(outfile, images)
            return outfile
        else:
            return None       

    def setTimestamp(self):
        nower = datetime.datetime.now()
        self.timestamp= str(nower.hour)+'-'+str(nower.minute)

    def reset(self):
        self.frame_buffer = []
        self.video_index = 1

def checkAndCreateDirectory(date):
    base_dir = '/home/teamjjj/Videos/'+date
    if not os.path.isdir(base_dir):
        try:
            os.makedirs(base_dir+'/light')
            os.makedirs(base_dir+'/pos')
            os.makedirs(base_dir+'/neg')
        except KeyboardInterrupt:
            raise
        except:
            e = sys.exc_info()[0]
            logging.warning('Exception: '+str(e))

def emailNotice(attachmentName):
    img_data = open(attachmentName, 'rb').read()
    msg = MIMEMultipart()
    msg['Subject'] = 'Hallway Video Preview'

    text = MIMEText("Sent to you via Python.")
    msg.attach(text)

    part = MIMEBase('application', "octet-stream")
    part.set_payload( img_data )
    encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(attachmentName))
    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com',587) #port 465 or 587
    server.ehlo()
    server.starttls()
    server.ehlo()
    
    # Get password from text file. Be sure to put your .txt file in the gitignore
    file = open('password.txt', 'r')
    password = [line.strip() for line in file].pop()
    file.close()
    
    server.login('jaroverrette@gmail.com', password)
    server.sendmail('jaroverrette@gmail.com','jaroverrette@gmail.com', msg.as_string())
    server.close()

def averageIntensity(image, starter):
    intensity = cv2.mean(image,mask=starter)[0]
    return intensity

# Set up logger
logger = logging.getLogger('doorcam')
logger.setLevel(logging.DEBUG)
now = datetime.datetime.now()
logname = str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'_'+str(now.hour)+'-'+str(now.minute)
fh = logging.FileHandler('/home/teamjjj/code/jarocam/logs/'+logname+'.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

# State machine
# 0 = checking every n seconds to check if light is on
# 1 = light is on but no motion detected
# 2 = motion detected in last m seconds   
state = 0

light_check_period = 0.3 # seconds to wait between frames when checking if light is on

no_motion_wait_period = 30 # If no motion for ten seconds, then send gif

# Motion Tracker
motionTracker = MotionTracker()

# Light Recorder
lr = LightRecorder()

threshold = 170 #intensity
starter = np.zeros([240, 240], dtype=np.uint8)
cv2.circle(starter, (120,120), 120, 255, -1)
cv2.rectangle(starter,(75,90),(130,150),0,-1)

with picamera.PiCamera() as camera:
    camera.resolution = (1280,720)
    time.sleep(2)

    while (1):
        start = time.time()
        image = np.empty((1280 * 720 * 3,), dtype=np.uint8)
        try:
            camera.capture(image, 'bgr')
        except KeyboardInterrupt:
            raise
        except:
            e = sys.exc_info()[0]
            logging.warning('Exception: '+str(e))
            continue
        image = image.reshape((720, 1280, 3))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY )
        image = image[230:470,550:790]
        # toshow = cv2.bitwise_and(imgBW, imgBW, mask=starter)
        # cv2.imshow('With the Light On',toshow)
        intensity = averageIntensity(image, starter)

        if state == 0:  # Light is off, checking for when it comes on
            if intensity >= threshold:
                logger.info('Light is on')
                state = 1 # Light has turned on
                lr.setTimestamp()
            #else:
                #time.sleep(light_check_period)
        elif state == 1:  # Light is on, checking for motion
            if intensity < threshold:
                logger.info('Light is off')
                state = 0 # Light has turned off
                motionTracker.reset()
                outfile = lr.saveVideo()
                lr.reset()
            else:
                # Call function to add image to motion tracker, returns true if motion detected
                motion, annotation = motionTracker.checkForMotion(image)
                if motion:
                    logger.info('Motion Detected')
                    state = 2
                elif motionTracker.framesSinceLastMotion() > 2*no_motion_wait_period:
                    motionTracker.resetMotionFrames()
                # Record when light is on
                lr.addImage(image, annotation)
        elif state == 2:  # Light is on, tracking and recording motion
            # Call function to add image to motion tracker, returns false if motion not detected
            # Save video of frames and send email if it's right neighbors after no motion for a while
            motion, annotation = motionTracker.checkForMotion(image)
            logger.info('Motion: '+str(motion)+' framesSinceLastMotion: '+str(motionTracker.framesSinceLastMotion()))   
            # Record when light is on
            lr.addImage(image, annotation)
            if not motion:
                if motionTracker.framesSinceLastMotion() > no_motion_wait_period:
                    if motionTracker.correctNeighbors():
                        outfile = motionTracker.saveMotion('pos')
    	                logger.info('Sending notification with '+outfile)
                        emailNotice(outfile)
                        motionTracker.resetMotionFrames()
                        state = 1
                    else:
                        outfile = motionTracker.saveMotion('neg')
    		        logger.info('Other motion, disregarding but saving to '+outfile)
                        motionTracker.resetMotionFrames()
                        state = 1 
            if intensity < threshold:
                logger.info('Light is off')
                state = 0 # Light has turned off
                motionTracker.reset()
                outfile = lr.saveVideo()
                lr.reset()

        elapsed = time.time() - start
        logger.debug('Intensity: '+str(intensity)+' FPS: '+str(1.0/elapsed)+' state: '+str(state))
             
