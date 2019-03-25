# jarocam
Train your dog to stay home alone with a raspberry pi (without bothering your neighbors)

record and identify video task on raspberry pi, send email notifier
The task of training a new puppy or anxious dog to stay home alone can often include barking.
While renters understand this difficulty, neighbors would appreciate you trained your dog when they are not home. 
This app helps notifies you when you can train your dog worry free!

The necessary hardware includes a rasberry pi and Raspberry Pi Camera. 
Any camera small enough to fit inside your door's peephole will suffice.
The contained app runs continuously on the raspberry pi.
It determines whether the light sensor in a hallway has been activated.
It records only when someone is in the hallway and the light sensore is activated.
It determines whether that person is most likely your next door neighbor based on the location of movement and activity.
It only sends you an email if the activity recorded through your peephole is most likely your next door neighbor entering or leaving.

Notification Email Details
Subject: Hallway Video Preview
Body: Sent to you via Python.
Attachment: a downsampled .mp4 file so that the user can determine whether it is appropriate for them to train their dog

The project jarocam is written in Python 3.

The primary modules used:
OpenCv (cv2)
picamera
logging
time
numpy
