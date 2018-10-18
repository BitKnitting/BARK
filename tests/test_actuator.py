import os
import time

import pytest
import adafruit_vl6180x
import board
import busio
import digitalio

closed_door_distance = int(os.getenv('close_door_mm'))


# Map possible GPIO keys to their board instance.
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
    time.sleep(30)
    open_io.value = False
    # The next sensor reading may be off a bit, so pad the expected distance
    print("\n\ntest_open(): at end of test...distance = {}".format(sensor.range))
    assert sensor.range >= closed_door_distance


def test_close(close_io, sensor):
    print("\n\ntest_open(): at start of test...distance = {}".format(sensor.range))
    if sensor.range > closed_door_distance + 5:
        close_io.value = True
        while sensor.range > closed_door_distance:
            pass
        close_io.value = False
        time.sleep(1)
    # The next sensor reading may be off a bit, so pad the expected distance
    print("\n\ntest_close(): at end of test...distance = {}".format(sensor.range))
    assert sensor.range <= closed_door_distance + 5
