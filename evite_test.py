import time
from threading import Timer
from math import floor

class Server:
    pass

class Scheduler:
    messages = None
    sender = None

    def __init__(self, sender):
        self.sender = sender
        self.messages = []

    def add_event(self, msg, recipients, start, repeat, interval):
        """Send message to recipients beginning at start for repeat intervals.

        msg -- the message to send (default "")
        recipients -- the recipients to send to (default [])
        start -- the time to start sending (default time.time())
        interval -- seconds between sendings (default 1)
        repeat -- the number of times to send (deault 3)"""
        for recipient in recipients:
            for delay in [floor(time.time() - start) + interval * repeat
                          for repeat in range(1, repeat + 1)]:
                print delay, self.sender, recipient, msg
                self.messages.append(Timer(delay, self.sender, (recipient, msg)))

    def start(self):
        for message in self.messages:
            message.start()

    def stop(self):
        for message in self.messages:
            message.cancel()
