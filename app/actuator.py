import os
import time
import RPi.GPIO as GPIO


class actuator():
    def __init__(self):
        self.open_pin = os.getenv("open_pin")
        self.close_pin = os.getenv("close_pin")
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.open_pin, GPIO.OUT)
        GPIO.setup(self.close_pin, GPIO.OUT)

    def open(self, nSeconds=1):
        GPIO.output(self.open_pin, True)
        time.sleep(nSeconds)
        GPIO.output(self.open_pin, False)

    def close(self, nSeconds=1):
        GPIO.output(self.close_pin, True)
        time.sleep(nSeconds)
        GPIO.output(self.close_pin, False)
