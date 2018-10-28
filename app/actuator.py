import os
import time
from collections import namedtuple

import adafruit_vl6180x
import board
import busio
import digitalio


from motion_detector import MotionDetector


# The Actuator class controls the linear actuator by opening, closing, or stopping it.
# It works with Adafruit's VL6180X Lidar sensor.  The sensor is used to provide feedback on closing.
# Close to the place where the door closes, there is a obstruction about 30mm from the sensor.  When
# the sensor tells us the door is 30mm away, closing the door stops.
# The Rasp Pi talks to the two relays that control opening/closing the Actuator through two GPIO pins.
# I use the .env file to provide these as environment variables, along with a few other environment
# variables.
class Actuator(MotionDetector):
    Button_states = namedtuple('Button_states', ['close', 'open', 'stop'])
    button_states = Button_states(0, 1, 2)
    Door_states = namedtuple('Door_states', ['closing', 'opening', 'idle'])
    door_states = Door_states(0, 1, 2)

    def __init__(self):
        # Initialize the Motion detector.
        super().__init__()
        # Set the initial button and door states.
        self._button_state = self.button_states.stop
        self._door_state = self.door_states.idle
        # Get the info from the environment on pins and distance.
        self.open_pin = self._init_pin(os.getenv('open_pin'))
        self.close_pin = self._init_pin(os.getenv('close_pin'))
        self.closed_door_distance = int(os.getenv('close_door_mm'))
        self.sensor = self._init_sensor()  # Do the Adafruit goo necessary to use the VL6180X BOB.

    @property
    def door_is_closed(self):
        if self.sensor.range <= self.closed_door_distance + 5 and self._door_state == self.door_states.idle:
            return True
        return False

    # Assumes a UI with 3 buttons.  close, open, stop.
    @property
    def button_state(self):
        return self._button_state

    # The UI sends in (via ajax) the value of the selected button.
    @button_state.setter
    def button_state(self, value):
        # From above, close = 0 (the least) and stop = 2 (the most).  Value between min/max.
        assert self.button_states.close <= value <= self.button_states.stop
        self._button_state = value

    def _close_door(self):
        if self._door_state == self.door_states.idle:
            if self.sensor.range > self.closed_door_distance + 5:
                self._door_state = self.door_states.closing
                distance_to_close = self.sensor.range
                self.log.print("_close(): Before closing...distance = {}".format(distance_to_close))
                self.close_pin.value = True
                while self.sensor.range > self.closed_door_distance:
                    pass
                self.close_pin.value = False
                self._door_state = self.door_states.idle
                distance_to_close = self.sensor.range
                self.log.print("_close(): After closing...distance = {}".format(distance_to_close))
            else:
                self.log.print("_close(): The door is already closed.  Distance is {}mm".format(self.sensor.range))

    def _open_door(self):
        if self._door_state == self.door_states.idle:
            distance_from_close = self.sensor.range
            self.log.print("_open_door(): At start...distance = {}".format(distance_from_close))
            # If the door is already open, close it.
            if distance_from_close > self.closed_door_distance + 5:
                self._door_state = self.door_states.closing
                self.close_pin.value = True
                while self.sensor.range > self.closed_door_distance:
                    pass
                self.close_pin.value = False
            # Open the door enough for the dogs to get out.
            seconds_to_open_door = int(os.getenv('seconds_to_open_door'))
            # I am assuming greater than 60 seconds to open the actuator is an error.
            if 60 >= seconds_to_open_door > 0:
                self._door_state = self.door_states.opening
                self.open_pin.value = True
                timeout_start = time.time()
                while time.time() < timeout_start + seconds_to_open_door:
                    pass
            self.open_pin.value = False
            self._door_state = self.door_states.idle
            distance_from_close = self.sensor.range
            self.log.print("_open_door(): At end ...distance = {}.".format(distance_from_close))

    # Set both relays off.
    def _stop(self):
        self._button_state = self.button_states.stop
        self.open_pin.value = False
        self.close_pin.value = False
        # Here the door is idle, but it could be partially opened.
        self._door_state = self.door_states.idle
        self.log.print('_stop(): In Stop.  Setting GPIO pins to False.  Set door_state back to IDLE')

    # Initialize the GPIO pins.  For now, I use 18 and 4.  Keeping in my Adafruit's Blinka
    # layer for Rasp Pi uses BCM numbering.
    def _init_pin(self, pin_str):
        try:
            board_pin = {'18': board.D18,
                         '4': board.D4
                         }[pin_str]
            pin = digitalio.DigitalInOut(board_pin)
            pin.direction = digitalio.Direction.OUTPUT
            return pin

        except KeyError:
            self.log.print('KeyError: pin **{}** not found in dict of pins.'.format(pin_str))
        return None

    # Adafruit's LIDAR sensor is used to figure out how far the door is from being closed.
    # It has a short distance detection range of a little over 100mm.
    def _init_sensor(self):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_vl6180x.VL6180X(i2c)
            return sensor
        except RuntimeError as e:
            self.log.print('{}'.format(e))
        return None

    # Make reading the logfile's entry on door state more readable.
    def door_state_str(self, door_state):
        if door_state not in self._door_states:
            return str(door_state)
        return {self.door_states.closing: 'CLOSING',
                self.door_states.opening: 'OPENING',
                self.door_states.idle: 'IDLE'
                }[door_state]

    # Same thing as with door state, make button state more readable.
    def button_state_str(self, button_state):
        if button_state not in self.button_states:
            return str(button_state)
        return {self.button_states.close: 'CLOSE',
                self.button_states.open: 'OPEN',
                self.button_states.stop: 'STOP'
                }[button_state]
