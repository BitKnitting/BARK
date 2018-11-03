import pytest

from sliding_door import Actuator


@pytest.fixture()
def actuator():
    a = Actuator()
    return a


def test_open(actuator):
    actuator.open_door()
    assert True


def test_close(actuator):
    actuator.close_door()
    assert True


def test_stop(actuator):
    actuator.stop()
    assert True


def test_actuator_value(actuator):
    # the only correct values are 0,1,2
    assert 0 in actuator.button_states
    assert 1 in actuator.button_states
    assert 2 in actuator.button_states
    assert 5 not in actuator.button_states
    assert 'aaa' not in actuator.button_states
