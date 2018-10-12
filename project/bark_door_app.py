import RPi.GPIO as GPIO
import time

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

open_pin = 12
close_pin = 7
GPIO.setmode(GPIO.BOARD)
GPIO.setup(open_pin, GPIO.OUT)
GPIO.setup(close_pin, GPIO.OUT)


def action_on_actuator(action_to_do, nSeconds):
    """0 = close, 1 = open, 2 = stop"""
    if action_to_do == 1 or action_to_do == 0:
        if action_to_do == 1:
            pin = open_pin
        else:
            pin = close_pin
        GPIO.output(pin, True)
        time.sleep(int(nSeconds[0]))
        GPIO.output(pin, False)
        return True
    #  Doesn't hurt to turn off both pins..
    if action_to_do == 2:
        GPIO.output(close_pin, False)
        GPIO.output(open_pin, False)
        return True
    return False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_open_close', methods=['POST'])
def get_open_close():
    action= request.get_json()
    if action_on_actuator(action['action'], action['seconds']):
        resp = jsonify(success=True)
    else:
        resp = jsonify(success=False)
    return resp


# if __name__ == "__main__":
#     # When debug=True, the debug service restarts after changes are made.
#     # This is very handy!
#     app.run(host='raspberrypi.home', port=8519, threaded=True)
#     # host = localhost when running on mac
#     # app.run(debug=True, host='localhost', port=9999oooo
