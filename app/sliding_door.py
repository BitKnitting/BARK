#
# The Sliding Door Class encapsulates the functionality needed to open and close the
# back door.
from actuator import Actuator


class SlidingDoor(Actuator):
    def __init__(self):
        # Initialize the Actuator instance.
        super().__init__()

    def do_action(self, button_action):
        """
        Given the state of the door and button, take the button action.
        """
        if button_action not in self.button_states:
            self.log.print("The button action {} is not one of the button states.".format(button_action))
            return
        # Take action if the door state is idle or the Stop button was pressed.
        # The stop button allows going from open to close (or close to open) before the full time it would take
        # to do so.  Multiple button clicks to the same button (unless it's the stop button) will be ignored.
        if self._door_state == self.door_states.idle or self._button_state == self.button_states.stop:
            if button_action == self.button_states.close:
                self._button_state = self.button_states.close
                self.log.print("...closing door")
                self._close_door()
            elif button_action == self.button_states.open:
                self._button_state == self.button_states.open
                self.log.print("...opening door")
                self._open_door()
            else:
                self._button_state = self.button_states.stop
                self.log.print("...stop")
                self._stop()
            return True

        self.log.print(
            "_handle_button_press(): nada.... door state {} button state {}".format(
                self.door_state_str(self.door_state_str(config.g_door_state)),
                self.button_state_str(self._button_state)))
        return False
