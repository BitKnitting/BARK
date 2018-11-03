#
# The HC-SR501 motion sensor is used to detect if the dogs are at the back door.  I get into more details
# on this particular pir sensor within the project's wiki.
#
#
from motion_detector import MotionDetector
#
# Note: According to https://bit.ly/1U3QVTZ , the pir sensor needs to be "plugged into" the rasp pi
# for at least a minute prior to using.
# I adjusted the time delay (how long the PIR pin remains HIGH - can be 5 secs to 5 min -


# GIVEN a HC-SR501 PIR sensor hooked up to the rasp pi and positioned so we can detect movement.
def test_motion():
    m = MotionDetector()
    while not m.motion_detected:
        pass
    assert True
