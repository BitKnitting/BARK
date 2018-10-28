#
#
# The HC-SR501 motion sensor is used to detect if the dogs are at the back door.  I get into more details
# on this particular pir sensor within the project's wiki.
import datetime
import os

import RPi.GPIO as GPIO
import requests

from handle_logging_lib import HandleLogging


# I am using the Rpi.GPIO module because of it's support of interrupt driven callbacks.


class MotionDetector:
    def __init__(self):
        self.log = HandleLogging()
        GPIO.setmode(GPIO.BCM)
        pin = int(os.getenv('pir_pin'))
        GPIO.setup(pin, GPIO.IN)
        # The event could have already been added.  This will cause a runtime error on add_event_detect
        # if the event hasn't been removed first.
        GPIO.remove_event_detect(pin)
        GPIO.add_event_detect(pin, GPIO.RISING)
        GPIO.add_event_callback(pin, self.movement_handler)
        # If the dogs are standing by the back door, no need to continually notify. Rather, notify if movement
        # continues past the last time a notification was sent.
        self.time_between_sending_notification = datetime.timedelta(minutes=1.)
        # Haven't sent a notification yet, so make sure we'll send the initial one.
        self.last_time_notification_sent = datetime.datetime.now() - self.time_between_sending_notification

    def movement_handler(self, pin):
        """
        The pin handling the PIR sensor has changed from LOW to HIGH.  But do we care?  We care if
        the door is closed,the actuator is idle, and we haven't just received a movement event.
         """
        if self.door_is_closed and self._door_state == self.door_states.idle:
            # If enough time has passed between sending a notification and the door conditions are met...
            if datetime.datetime.now() - self.last_time_notification_sent > self.time_between_sending_notification:
                # Send a notification to our phone.
                requests.get(
                    'https://maker.ifttt.com/trigger/Barking/with/key/e-deNt3oqThDXl2nSB4NAlNeImbIo_s8V1cnZDxNxWn')
                self.log.print("Sent a movement detection notification.")
                self.last_time_notification_sent = datetime.datetime.now()
