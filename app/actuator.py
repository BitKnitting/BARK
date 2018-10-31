import os
import time
from collections import namedtuple

import adafruit_vl6180x
import board
import busio
import digitalio

from handle_logging_lib import HandleLogging


# Todo: app freezes after calls to range sensor.  This was working before, but now freezes.

# The Actuator class controls the linear actuator by opening, closing, or stopping it.

class Actuator():
    # Class variables shared by all instances
    Button_states = namedtuple('Button_states', ['close', 'open', 'stop'])
    button_states = Button_states(0, 1, 2)
    Door_states = namedtuple('Door_states', ['closing', 'opening', 'idle'])
    door_states = Door_states(0, 1, 2)

    def __init__(self):
        self.log = HandleLogging()
        # Variables unique to each instance
        # Set the initial button and door states.
        self._button_state = self.button_states.stop
        self._door_state = self.door_states.idle
        # Get the info from the environment on pins and distance.
        self.open_pin = self._init_pin(os.getenv('open_pin'))
        self.close_pin = self._init_pin(os.getenv('close_pin'))
        self.closed_door_distance = int(os.getenv('close_door_mm'))
        self.sensor = self._init_sensor()

    def _init_sensor(self):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_vl6180x.VL6180X(i2c)
            self.log.print('Sensor has been initialized.')
            return sensor
        except RuntimeError as e:
            self.log.print('{}'.format(e))
        return None

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

    def do_action(self, button_action):
        # Making sure we get a button action we know how to handle.
        if button_action not in self.button_states:
            self.log.print("The button action {} is not one of the button states.".format(button_action))
            return
            # Take action if the door state is idle or the Stop button was pressed.
            # The stop button allows going from open to close (or close to open) before the full time it would take
            # to do so.  Multiple button clicks to the same button (unless it's the stop button) will be ignored.
        if self._door_state == self.door_states.idle or button_action == self.button_states.stop:
            # The door state is idle.  Was the CLOSE button pressed?
            if button_action == self.button_states.close:
                # Set the button state to closing.
                self._button_state = self.button_states.close
                self.log.print("...closing door")
                # Close the door.
                self._close_door()
            # The door state is idle.  Was the OPEN button pressed?
            elif button_action == self.button_states.open:
                # Set the button state to opening.
                self._button_state = self.button_states.open
                self.log.print("...opening door")
                # Open the door.
                self._open_door()
            # The STOP button was pressed.
            else:
                # Set the button state to stopped.
                self._button_state = self.button_states.stop
                self.log.print("...stop")
                # Stop opening or closing, reset whatever needs to be reset.
                self._stop()
        # Multiple clicks to OPEN or CLOSED while in the process of opening or closing.
        else:
            self.log.print(
                "_handle_button_press(): nada.... door state {} button state {}".format(
                    self.door_state_str(self.door_state_str(self.door_state)),
                    self.button_state_str(self._button_state)))

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
