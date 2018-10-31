"""
Unit test the distance sensor.
Distance is interesting for determining if the
slide door is shut.  It is less interesting how much the door is open.
"""
import adafruit_vl6180x
import board
import busio


def test_i2c():
    i2c = busio.I2C(board.SCL, board.SDA)
    assert isinstance(i2c, busio.I2C)


def test_sensor_status():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_vl6180x.VL6180X(i2c)
    assert isinstance(sensor, adafruit_vl6180x.VL6180X)
    # See the vl6180x datasheet (Table 12)
    # https://www.st.com/resource/en/datasheet/vl6180x.pdf
    # The error codes and description:
    # 0     - No Error
    # 1-5   - System error
    # 6     - Early convergent estimate failed
    # 7     - System did not converge before max convergence time limit
    # 8     - Ignore threshold check failed
    # 9-10  - Not used
    # 11    - Ambient conditions to high.  Measurement not valid.
    # 12-14 - Range < 0.  If the target is very close (0-10mm) and the offset
    #         is not correctly calibrated it could lead to a small
    #         negative value
    # 13/15 - Range value out of range. This occurs when the
    #         target is detected by the device but is placed at a
    #         high distance (> 200mm) resulting in internal
    #         variable overflow.
    # 16    - Distance filtered by Wrap Around Filter (WAF).
    #         Occurs when a high reflectance target is
    #         detected between 600mm to 1.2m
    # 17    - Not used
    # 18    - Error returned by
    #         VL6180x_RangeGetMeasurementIfReady()
    #         when ranging data is not ready.
    assert 0 == sensor.range_status


# Measures up to 200mm, although spec'd for only up to 100mm.
# Returns 255 if measurement > 255mm. If the distance is much > or
# measurements are made in low light, an error will be returned.
# Note from the datasheet:  Ranging beyond 100mm is dependent on
# target reflectance and external conditions (ambient light level,
# temperature, voltage)
def test_distance():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_vl6180x.VL6180X(i2c)
    print("\n\ntest_distance(): sensor range = " + str(sensor.range) + "mm")
    assert (0 < sensor.range <= 255)


# Check if there is any problem constantly instantiating stuff.
def test_repeat_distance():
    for _ in range(20):
        test_distance()


# I could see a use for knowing the light level and then turning on a light.
# Currently not using.
def test_lux():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_vl6180x.VL6180X(i2c)
    lux = sensor.read_lux(adafruit_vl6180x.ALS_GAIN_1)
    print('\n\ntest_lux(): Light (1x gain): {0}lux'.format(lux))
    # https://www.st.com/resource/en/datasheet/vl6180x.pdf
    # Table 1, Technical specification
    # < 1 Lux up to 100 kLux(2) 16-bit output(3) 8 manual gain settings
    assert (0 <= lux <= 100000)
