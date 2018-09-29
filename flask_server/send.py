import os
import sys
LIB_PATH = os.environ['LADYBUG_LIB_PATH']
sys.path.append(LIB_PATH)
from RFM69_messages_lib import RFM69Messages

rf69 = RFM69Messages()
while True:
    # # Send a packet.  Note you can only send a packet up to 60 bytes in length.
    # # This is a limitation of the radio packet size, so if you need to send larger
    # # amounts of data you will need to break it into smaller send calls.  Each send
    # # call will wait for the previous one to finish before continuing.
    rf69.radio.send('Hello world!\r\n')
    print('Sent hello world message!')

print("done")
