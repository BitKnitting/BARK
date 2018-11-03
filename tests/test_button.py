#
# A button is placed where the door is closed.  When the door is closed, the button
# is pressed.
#
import datetime
import os

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
# Class variables shared by all instances
button_pin = int(os.getenv('button_pin'))
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def test_button_pressed():
    import time

    now = datetime.datetime.now()
    end_of_test = datetime.timedelta(seconds=30)
    while datetime.datetime.now() < now + end_of_test:
        button_state = GPIO.input(button_pin)
        if button_state:
            assert True
            print('\n\nDoor closed.')
            break
        time.sleep(0.2)
    if not button_state:
        assert False
    GPIO.cleanup()
