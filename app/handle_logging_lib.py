import inspect
import logging
import os
import sys


class HandleLogging:

    def __init__(self):
        logfile = os.getenv("logfile")
        # set DEBUG for everything
        # In the docs: https://docs.python.org/3/library/logging.html
        # 16.6.7 Talks about LogRecord Attributes.  I am using this to
        # provide date/time info...i tried a few others to get stack
        # info, however returned info on this module.  So used inspect.
        logging.basicConfig(filename=logfile, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s  %(message)s',
                            datefmt='%b %-d,%Y %H:%M')

    def _make_message(self, message):
        # getting to the caller's caller since
        # this function is called from within
        (filepathname, line_number,
         name, lines, index) = inspect.getframeinfo(sys._getframe(2))
        code_info_str = ": {} - {} - {} : ".format(os.path.basename(filepathname), line_number, name)
        return (code_info_str + message)

    def print(self, message):
        logging.info(self._make_message(message))
