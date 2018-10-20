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
        self.open_pin = self._init_pin(os.getenv('open_pin'))
        self.close_pin = self._init_pin(os.getenv('close_pin'))
        self.closed_door_distance = int(os.getenv('close_door_mm'))
        self.sensor = self._init_sensor()
        self.log = HandleLogging()
        self._button_state = button_state

    # Assumes a UI with 3 buttons.  close, open, stop.
    @property
    def button_state(self):
        return self._button_state

    # The UI sends in (via ajax) the value of the selected button.
    @button_state.setter
    def button_state(self, value):
        assert 0 <= value <= 2
        self._button_state = value

    def handle_button_press(self):
        """
        Given the button_state, either open, close, or stop opening/closing the sliding door.
        (once again) check to make sure we have a valid button state.
        """
        if self._button_state not in self.button_states:
            error_str = "Error! button state is " + str(self._button_state)
            ". Expecting a value of 0 (close), 1 (open), 2 (stop)"
            self.log.print(error_str)
            return False
        if self._button_state == self.button_states.close:
            self._close()
        elif self._button_state == self.button_states.open:
            self._open()
        else:
            self._stop()
        return True

    def _close(self):
        self.log.print("_close(): Before closing...distance = {}".format(self.sensor.range))
        if self.sensor.range > self.closed_door_distance + 5:
            self.close_pin.value = True
            while self.sensor.range > self.closed_door_distance:
                pass
            self.close_pin.value = False
            time.sleep(1)
        # The next sensor reading may be off a bit, so pad the expected distance
        self.log.print("_close(): After closing...distance = {}".format(self.sensor.range))

    def _open(self):
        # If the door is already open, close it.
        self.log.print("_open(): At start...distance = {}".format(self.sensor.range))
        if self.sensor.range > self.closed_door_distance + 5:
            self.close_pin.value = True
            while self.sensor.range > self.closed_door_distance:
                pass
            self.close_pin.value = False
        # settle a bit.
        time.sleep(1)
        # Open the door enough for the dogs to get out.
        self.open_pin.value = True
        seconds_to_open_door = int(os.getenv('seconds_to_open_door'))
        assert 0 < seconds_to_open_door
        time.sleep(seconds_to_open_door)
        self.open_pin.value = False
        # The next sensor reading may be off a bit, so pad the expected distance
        print("_open(): At end ...distance = {}".format(self.sensor.range))

    def _stop(self):
        self.open_pin.value = False
        self.close_pin.value = False

    def _init_pin(self, pin_str):
        board_pin = {'18': board.D18,
                     '4': board.D4
                     }[pin_str]
        pin = digitalio.DigitalInOut(board_pin)
        pin.direction = digitalio.Direction.OUTPUT
        self.already_init = True
        return pin

    def _init_sensor(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        return adafruit_vl6180x.VL6180X(i2c)
