from flask import Flask, render_template, request, jsonify

import os
import sys
import time

LIB_PATH = os.environ['LADYBUG_LIB_PATH']
sys.path.append(LIB_PATH)
from RFM69_messages_lib import RFM69Messages

rf69 = RFM69Messages()

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')
    # return('hello')


@app.route('/get_open_close', methods=['POST'])
def get_open_close():
    open_or_close = request.get_json()
    # open_or_close will be {open:1} for open or {open:0} for close
    send_open_or_close(open_or_close['open'])
    resp = jsonify(success=True)
    return resp


def send_open_or_close(open):
    packet_to_send = [rf69._ACTUATOR,open]
    received_packet = False
    while True:
        if received_packet:
            break
        rf69.radio.send(bytearray(packet_to_send))
        #rf69.radio.send('Hello world!\r\n')
        print('Sent hello world message!')
        time.sleep(1)
    # rf69.radio.send(bytearray(packet_to_send))
    rf69.radio.receive_begin(keep_listening=True, callback=receive_done)

def receive_done(packet):
    received_packet = True
    print("received packet {}".format(packet))



if __name__ == "__main__":
    # When debug=True, the debug service restarts after changes are made.
    # This is very handy!
    # Using Remot3.it.  Following lead from this question/answer:
    # http://forum.weaved.com/t/streaming-video-on-web-page/292/2
    app.run(host='raspberrypi.home', port=8519, debug=True, threaded=True)
# host = localhost when running on mac
# app.run(debug=True, host='localhost', port=9999)
