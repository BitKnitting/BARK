#
# The HC-SR501 motion sensor is used to detect if the dogs are at the back door.  I get into more details
# on this particular pir sensor within the project's wiki.
#
# These tests make sure the pir sensor is working as expected.  What is expected is defined within a test.
#
import os
import time

# I am using the Rpi.GPIO module because of it's support of interrupt driven callbacks.
import RPi.GPIO as GPIO
import pytest

seconds_to_test_motion = 10


#
# Note: According to https://bit.ly/1U3QVTZ , the pir sensor needs to be "plugged into" the rasp pi
# for at least a minute prior to using.
# I adjusted the time delay (how long the PIR pin remains HIGH - can be 5 secs to 5 min -


# GIVEN a HC-SR501 PIR sensor hooked up to the rasp pi and positioned so we can detect movement.
@pytest.fixture()
def pir_pin():
    pin_str = os.getenv('pir_pin')
    # The pir sensor is read from BCM pin 23.
    assert (pin_str == '23')
    pin = int(pin_str)
    # Set the pin numbering mode to BCM (yah - I find rasp pi's number scheme kinda confusing...)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN)
    return pin


# GIVEN a call back function set to the GPIO pin receivng HIGH when motion detected from the PIR sensor...


def test_detect_motion(pir_pin):
    motion_detected = False
    # Run for a short time.
    timeout_start = time.time()
    while time.time() < timeout_start + seconds_to_test_motion:
        # WHEN the pir pin goes to HIGH...
        if GPIO.input(pir_pin):
            motion_detected = True
            break
    # THEN movement is detected.
    assert motion_detected, True


# I COULD NOT get callback to work.
def movement_handler(pin):
    print("in movement handler.   Pin: {}".format(pin))
    assert True


def test_motion_callback(pir_pin):
    GPIO.remove_event_detect(pir_pin)
    GPIO.add_event_detect(pir_pin, GPIO.RISING)
    GPIO.add_event_callback(pir_pin, movement_handler)

    while True:
        pass


