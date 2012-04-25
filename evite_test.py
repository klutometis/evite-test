import time
import simplejson as json
from threading import Timer
from math import floor
from flask import Flask, request
from threading import Thread
from multiprocessing import Process
import sys

app = Flask(__name__)
events = None
scheduler = None

def init_app(sender=lambda x: x):
    global events, scheduler
    events = []
    scheduler = Scheduler(sender)

@app.route('/events', methods=['POST'])
def create_event():
    global events, scheduler
    event = request.json
    events.append(event)
    event.update({'immediate': True})
    scheduler.add_event(**event)
    return json.dumps({'id': str(len(events) - 1)})

@app.route('/events/<int:id>')
def get_event(id):
    global events
    return json.dumps(events[id])

class Server:
    sender = None
    port = None
    server = None

    def __init__(self, sender, port):
        self.sender = sender
        self.port = port

    def start(self):
        init_app(self.sender)
        self.server = Process(target=lambda: app.run(port=self.port, debug=True))
        self.server.start()

        # Wait for server to start
        time.sleep(1)

    def stop(self):
        self.server.terminate()

class Scheduler:
    messages = None
    sender = None

    def __init__(self, sender):
        self.sender = sender
        self.messages = []

    def add_event(self, msg, recipients, start, repeat, interval, immediate=False):
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
                print >> sys.stderr, 'add_event/sender', id(self.sender)
                message = Timer(delay, self.sender, (recipient, msg))
                if immediate:
                    message.start()
                else:
                    self.messages.append(message)

    def start(self):
        for message in self.messages:
            message.start()

    def stop(self):
        for message in self.messages:
            message.cancel()

if __name__ == '__main__':
    init_app()
    app.run(debug=True, port=8080)
