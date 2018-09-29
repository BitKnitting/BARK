import RPi.GPIO as GPIO
import time

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

open_pin = 7
close_pin = 12
GPIO.setmode(GPIO.BOARD)
GPIO.setup(open_pin, GPIO.OUT)
GPIO.setup(close_pin, GPIO.OUT)


def turn_on_off_actuator(open):
    """1 = open, 0 = close"""
    if open == 1 or open == 0:
        if open == 1:
            pin = open_pin
        else:
            pin = close_pin
        GPIO.output(pin, True)
        time.sleep(10)
        GPIO.output(pin, False)
        return True
    return False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_open_close', methods=['POST'])
def get_open_close():
    which_button = request.get_json()
    if turn_on_off_actuator(which_button['open']):
        resp = jsonify(success=True)
    else:
        resp = jsonify(success=False)
    return resp


if __name__ == "__main__":
    # When debug=True, the debug service restarts after changes are made.
    # This is very handy!
    app.run(host='raspberrypi.home', port=8519, debug=True, threaded=True)
    # host = localhost when running on mac
    # app.run(debug=True, host='localhost', port=9999)
