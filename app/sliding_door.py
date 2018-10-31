#
# The Sliding Door Class encapsulates the functionality needed to open and close the
# back door.
from actuator import Actuator
from motion_detector import MotionDetector


class SlidingDoor():
    def __init__(self):
        # A sliding door is open and closed using an Actuator and a distance sensor.
        self.door_controller = Actuator()

        # A Motion detector is used to know when a dog wants to go out.  So activate the motion detector.
        MotionDetector()

    def do_action(self, button_action):
        """
        Given the state of the door and button, take the button action.
        """
        self.door_controller.do_action(button_action)
