import os
import time
from collections import namedtuple

import adafruit_vl6180x
import board
import busio
import digitalio

from handle_logging_lib import HandleLogging


# The Actuator class controls the linear actuator by opening, closing, or stopping it.
# It works with Adafruit's VL6180X Lidar sensor.  The sensor is used to provide feedback on closing.
# Close to the place where the door closes, there is a obstruction about 30mm from the sensor.  When
# the sensor tells us the door is 30mm away, closing the door stops.
# The Rasp Pi talks to the two relays that control opening/closing the Actuator through two GPIO pins.
# I use the .env file to provide these as environment variables, along with a few other environment
# variables.
class Actuator:
    def __init__(self, button_state=0):
        Button_states = namedtuple('Button_states', ['close', 'open', 'stop'])
        self.button_states = Button_states(0, 1, 2)
        self._button_state = button_state
        # There is no previous button state the first time through.
        self._prev_button_state = -1
        Door_states = namedtuple('Door_states', ['close', 'open', 'stop', 'idle'])
        self.door_states = Door_states(0, 1, 2, 3)
        self._door_state = self.door_states.idle
        self.open_pin = self._init_pin(os.getenv('open_pin'))
        self.close_pin = self._init_pin(os.getenv('close_pin'))
        self.closed_door_distance = int(os.getenv('close_door_mm'))
        self.sensor = self._init_sensor()  # Do the Adafruit goo necessary to use the VL6180X BOB.
        self.log = HandleLogging()  # A simple logging library I wrote that works ok for me.

    # Assumes a UI with 3 buttons.  close, open, stop.
    @property
    def button_state(self):
        return self._button_state

    # The UI sends in (via ajax) the value of the selected button.
    @button_state.setter
    def button_state(self, value):
        assert 0 <= value <= 2
        self._prev_button_state = self._button_state
        self._button_state = value

    def handle_button_press(self):
        """
        Given the button_state, either open, close, or stop opening/closing the sliding door.
        (once again) check to make sure we have a valid button state.
        """
        # Ignore the button press if this is a repeat press, unless the door state is idle...because
        # we could have missed an action.
        if self._button_state == self._prev_button_state and self._door_state != self.door_states.idle:
            self.log.print(
                "_handle_button_press(): Current button state {} == previous button state {}".format(
                    self.button_state_str(self._button_state), self.button_state_str(self._prev_button_state)))
            return False
        # It is ok to take action if the door state is idle or the Stop button was pressed.
        if self._door_state == self.door_states.idle or self._button_state == self.button_states.stop:
            self.log.print(
                "_handle_button_press(): yippee.... door state {} button state {}".format(
                    self.door_state_str(self._door_state), self.button_state_str(self._button_state)))
            if self._button_state == self.button_states.close:
                self._close()
            elif self._button_state == self.button_states.open:
                self._open_door()
            else:
                self._stop()
            return True
        self.log.print(
            "_handle_button_press(): nada.... door state {} button state {}".format(
                self.door_state_str(self.door_state_str(self._door_state)), self.button_state_str(self._button_state)))
        return False

    def _close(self):

        if self.sensor.range > self.closed_door_distance + 5:
            self.log.print("_close(): Changing door state to {}.".format(self.door_state_str(self._door_state)))
            self._door_state = self.door_states.close
            self.log.print("_close(): Before closing...distance = {}".format(self.sensor.range))
            self.close_pin.value = True
            while self.sensor.range > self.closed_door_distance:
                pass
            self.close_pin.value = False
            self._door_state = self.door_states.idle
            self.log.print(
                "_close(): After closing...distance = {}.  Door state = {}".format(self.sensor.range,
                                                                                   self.door_state_str(
                                                                                       self._door_state)))
        else:
            self.log.print("_close(): The door is already closed.  Distance is {}mm".format(self.sensor.range))

    def _open_door(self):
        self._door_state = self.door_states.open
        self.log.print("_open_door(): Changing door state to OPEN")
        # If the door is already open, close it.
        self.log.print("_open_door(): At start...distance = {}".format(self.sensor.range))
        if self.sensor.range > self.closed_door_distance + 5:
            self.close_pin.value = True
            while self.sensor.range > self.closed_door_distance:
                pass
            self.close_pin.value = False
        # Open the door enough for the dogs to get out.
        seconds_to_open_door = int(os.getenv('seconds_to_open_door'))
        # I am assuming greater than 60 seconds to open the actuator is an error.
        if 60 >= seconds_to_open_door > 0:
            self.open_pin.value = True
            timeout_start = time.time()
            while time.time() < timeout_start + seconds_to_open_door:
                pass
        self.open_pin.value = False
        # The next sensor reading may be off a bit, so pad the expected distance
        self._door_state = self.door_states.idle
        print("_open_door(): At end ...distance = {}.  Door state = IDLE.".format(self.sensor.range))

    # Set both relays off.
    def _stop(self):
        self._door_state = self.door_states.stop
        self.open_pin.value = False
        self.close_pin.value = False
        self._door_state = self.door_states.idle
        self.log.print('_stop(): In Stop.  Setting GPIO pins to False.  Set door_state back to {}'.format(
            self.door_state_str(self._door_state)))

    # Initialize the GPIO pins.  For now, I use 18 and 4.  Keeping in my Adafruit's Blinka
    # layer for Rasp Pi uses BCM numbering.
    def _init_pin(self, pin_str):
        board_pin = {'18': board.D18,
                     '4': board.D4
                     }[pin_str]
        pin = digitalio.DigitalInOut(board_pin)
        pin.direction = digitalio.Direction.OUTPUT
        return pin

    # Adafruit's LIDAR sensor is used to figure out how far the door is from being closed.
    # It has a short distance detection range of a little over 100mm.
    def _init_sensor(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        return adafruit_vl6180x.VL6180X(i2c)

    # Make reading the logfile's entry on door state more readable.
    def door_state_str(self, door_state):
        if door_state not in self.door_states:
            return "UNKNOWN"
        return {self.door_states.close: 'CLOSE',
                self.door_states.open: 'OPEN',
                self.door_states.stop: 'STOP',
                self.door_states.idle: 'IDLE'
                }[door_state]

    # Same thing as with door state, make button state more readable.
    def button_state_str(self, button_state):
        if button_state not in self.button_states:
            return "UNKNOWN"
        return {self.button_states.close: 'CLOSE',
                self.button_states.open: 'OPEN',
                self.button_states.stop: 'STOP'
                }[button_state]
