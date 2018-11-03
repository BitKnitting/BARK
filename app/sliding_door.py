import datetime
import os
from collections import namedtuple

import RPi.GPIO as GPIO
import requests

from handle_logging_lib import HandleLogging


# The Actuator class controls the linear actuator by opening, closing, or stopping it.

class SlidingDoor:
    seconds_to_open_door = int(os.getenv('seconds_to_open_door'))
    Button_states = namedtuple('Button_states', ['close', 'open', 'stop'])
    button_states = Button_states(0, 1, 2)
    Door_states = namedtuple('Door_states', ['closing', 'opening', 'idle'])
    door_states = Door_states(0, 1, 2)

    def __init__(self):
        self._init_GPIO()
        self._init_motion()
        # Variables unique to each instance
        self.log = HandleLogging()
        # Set the initial button and door states.
        self._button_state = self.button_states.stop
        self.door_state = self.door_states.idle
        self.log.print("__init__ CHANGING DOOR STATE TO IDLE")

    def _init_GPIO(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.open_pin = int(os.getenv('open_pin'))
        GPIO.setup(self.open_pin, GPIO.OUT)
        self.close_pin = int(os.getenv('close_pin'))
        GPIO.setup(self.close_pin, GPIO.OUT)
        self.pir_pin = int(os.getenv('pir_pin'))
        GPIO.setup(self.pir_pin, GPIO.IN)

    def _init_motion(self):
        # The event could have already been added.  This will cause a runtime error on add_event_detect
        # if the event hasn't been removed first.
        GPIO.remove_event_detect(self.pir_pin)
        GPIO.add_event_detect(self.pir_pin, GPIO.RISING)
        GPIO.add_event_callback(self.pir_pin, self.movement_handler)
        # If the dogs are standing by the back door, or opening/closing causes movement detection, there is
        # no need to continually notify. After time_between_sending_notifications, notify of a movement.
        time_between = float(os.getenv('time_between_detecting_motion'))
        self.time_between_sending_notification = datetime.timedelta(minutes=time_between)
        # Haven't sent a notification yet, so make sure we'll send the initial one.
        self.start_notification_timer = datetime.datetime.now() - self.time_between_sending_notification
        self.motion_detected = False

    def check_and_send(self):
        # If enough time has passed between sending a notification...
        delta_time = datetime.datetime.now() - self.start_notification_timer
        self.log.print("Door state: {} delta time: {}".format(self.door_state, delta_time))
        if self.door_state == self.door_states.idle and delta_time > self.time_between_sending_notification:
            # Send a notification to our phone.
            requests.get(
                'https://maker.ifttt.com/trigger/Barking/with/key/e-deNt3oqThDXl2nSB4NAlNeImbIo_s8V1cnZDxNxWn')
            self.log.print(
                "Sent a movement detection notification.  Door state: {} delta time: {}".format(self.door_state,
                                                                                                delta_time))
            self.start_notification_timer = datetime.datetime.now()
            self.motion_detected = True
        else:
            self.motion_detected = False

    def movement_handler(self, pin):
        """
        The movement_handler is the callback set up by call to  GPIO.add_event_callback.  It is called when the pir_pin
        goes from LOW to HIGH (i.e.: GPIO.add_event_detect(pin,GPIO.RISING)
        """
        self.check_and_send()

    def do_action(self, button_action):
        # Making sure we get a button action we know how to handle.
        if button_action not in self.button_states:
            self.log.print("The button action {} is not one of the button states.".format(button_action))
            return
            # Take action if the door state is idle or the Stop button was pressed.
            # The stop button allows going from open to close (or close to open) before the full time it would take
            # to do so.  Multiple button clicks to the same button (unless it's the stop button) will be ignored.
        if self.door_state == self.door_states.idle or button_action == self.button_states.stop:
            # The door state is idle.  Was the CLOSE button pressed?
            if button_action == self.button_states.close:
                # Set the button state to closing.
                self._button_state = self.button_states.close
                # Close the door.
                self.close_door()
            # The door state is idle.  Was the OPEN button pressed?
            elif button_action == self.button_states.open:
                # Set the button state to opening.
                self._button_state = self.button_states.open
                # Open the door.
                self.open_door()
            # The STOP button was pressed.
            else:
                # Set the button state to stopped.
                self._button_state = self.button_states.stop
                self.log.print("...stop")
                # Stop opening or closing, reset whatever needs to be reset.
                self.stop()
        # Multiple clicks to OPEN or CLOSED while in the process of opening or closing.
        else:
            self.log.print(
                "_handle_button_press(): nada.... door state {} button state {}".format(
                    self.door_state_str(self.door_state_str(self.door_state)),
                    self.button_state_str(self._button_state)))

    def close_door(self):
        self.door_state = self.door_states.closing
        self.log.print("close_door: CHANGING DOOR STATE TO CLOSE.  Door state: {}".format(self.door_state))
        self.move_door(self.close_pin)

    def open_door(self):
        self.door_state = self.door_states.opening
        self.log.print("open_door: CHANGING DOOR STATE TO OPEN.  Door state: {}".format(self.door_state))
        self.move_door(self.open_pin)

    # Set both relays off.
    def stop(self):
        self._button_state = self.button_states.stop
        self.turn_off_switches()
        # Here the door is set to idle, but it could be partially opened.
        self.door_state = self.door_states.idle
        self.log.print("stop: CHANGING DOOR STATE TO IDLE.")
        self.start_notification_timer = datetime.datetime.now()

    def turn_off_switches(self):
        GPIO.output(self.open_pin, False)
        GPIO.output(self.close_pin, False)

    def move_door(self, pin):
        self.turn_off_switches()
        GPIO.output(pin, True)
        self.wait(self.seconds_to_open_door)
        GPIO.output(pin, False)

    def wait(self, s):
        now = datetime.datetime.now()
        end_of_open_time = datetime.timedelta(seconds=s)
        while datetime.datetime.now() < now + end_of_open_time:
            pass
        self.door_state = self.door_states.idle
        self.log.print("wait: CHANGING DOOR STATE TO IDLE.")
        self.start_notification_timer = datetime.datetime.now()

    # Make reading the logfile's entry on door state more readable.
    def door_state_str(self, door_state):
        if door_state not in self.door_states:
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
