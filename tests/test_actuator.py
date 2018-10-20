import os
import time

import pytest
import adafruit_vl6180x
import board
import busio
import digitalio

from actuator import Actuator

# Determined through experiment the door is closed when the distance sensor reads close_door_mm mm from the
# 'flap' working as the obstructor.
closed_door_distance = int(os.getenv('close_door_mm'))


# Map possible GPIO keys to their board instance.
# I currently know I am using 18 or 4 (Adafruit's Blinka uses BCM numbering)
def get_board(pin):
    assert pin == '18' or pin == '4'
    return {'18': board.D18,
            '4': board.D4
            }[pin]


@pytest.fixture()
def open_io():
    open_pin_str = os.getenv('open_pin')
    open_pin_board = get_board(open_pin_str)
    open_pin = digitalio.DigitalInOut(open_pin_board)
    assert isinstance(open_pin, digitalio.DigitalInOut)
    open_pin.direction = digitalio.Direction.OUTPUT
    return open_pin


@pytest.fixture()
def close_io():
    close_pin_str = os.getenv('close_pin')
    close_pin_board = get_board(close_pin_str)
    close_pin = digitalio.DigitalInOut(close_pin_board)
    assert isinstance(close_pin, digitalio.DigitalInOut)
    close_pin.direction = digitalio.Direction.OUTPUT
    return close_pin


@pytest.fixture()
def sensor():
    i2c = busio.I2C(board.SCL, board.SDA)
    assert isinstance(i2c, busio.I2C)
    s = adafruit_vl6180x.VL6180X(i2c)
    assert isinstance(s, adafruit_vl6180x.VL6180X)
    return s


# Test opening the door (door must be unlocked).
# If the door is open, close it first.  This is because I can't tell how far the door is
# currently opened because the distance sensor is only good a little past 100mm.
def test_open(open_io, close_io, sensor):
    # If the door is already open, close it.
    print("\n\ntest_open(): at start of test...distance = {}".format(sensor.range))
    if sensor.range > closed_door_distance + 5:
        close_io.value = True
        while sensor.range > closed_door_distance:
            pass
        close_io.value = False
        # settle a bit.
        time.sleep(2)
    # Open the door enough for the dogs to get out.  This is roughly
    # 30 seconds.  Too bad the sensor is only "good" for ~ 100mm.
    open_io.value = True
    seconds_to_open_door = int(os.getenv('seconds_to_open_door'))
    assert 0 < seconds_to_open_door
    time.sleep(seconds_to_open_door)
    open_io.value = False
    # The next sensor reading may be off a bit, so pad the expected distance
    print("\n\ntest_open(): at end of test...distance = {}".format(sensor.range))
    assert sensor.range >= closed_door_distance


def test_close(close_io, sensor):
    print("\n\ntest_close(): at start of test...distance = {}".format(sensor.range))
    if sensor.range > closed_door_distance + 5:
        close_io.value = True
        while sensor.range > closed_door_distance:
            pass
        close_io.value = False
        time.sleep(1)
    # The next sensor reading may be off a bit, so pad the expected distance
    print("\n\ntest_close(): at end of test...distance = {}".format(sensor.range))
    assert sensor.range <= closed_door_distance + 5


def test_button_value():
    actuator = Actuator()
    # the only correct values are 0,1,2
    assert False == actuator.button_check('adsfasdfasdf')
    assert False == actuator.button_check(['a', 'b'])
    assert True == actuator.button_check(0)
    assert True == actuator.button_check(1)
    assert True == actuator.button_check(2)
    assert False == actuator.button_check(3)
    assert False == actuator.button_check(3)
