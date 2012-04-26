import time
import simplejson as json
from threading import Timer
from flask import Flask, request
from threading import Thread
from multiprocessing import Process, Queue
import sys

app = Flask(__name__)
events = None
queue = None

def init_app():
    global events, queue
    queue = Queue()
    events = []

@app.route('/events', methods=['POST'])
def create_event():
    global events, queue
    event = request.json
    events.append(event)
    # Should we make this non-blocking?
    queue.put(event)
    return json.dumps({'id': str(len(events) - 1)})

@app.route('/events/<int:id>')
def get_event(id):
    global events
    return json.dumps(events[id])

class Server:
    port = None
    server = None
    scheduler = None

    def __init__(self, sender, port):
        self.port = port
        self.scheduler = Scheduler(sender)

    def send_from_queue(self):
        event = queue.get()
        self.scheduler.add_event(immediate=True, **event)
        self.send_from_queue()

    def start(self):
        init_app()
        self.server = Process(target=app.run,
                              kwargs={'port': self.port})
        self.server.start()

        # Wait for server to start
        time.sleep(1)

        # Start thread that monitors the queue and sends when we get
        # new events.
        send_from_queue = Thread(target=self.send_from_queue)
        send_from_queue.daemon = True
        send_from_queue.start()

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
            for delay in [time.time() - start + interval * repeat
                          for repeat in range(1, repeat + 1)]:
                print delay, self.sender, recipient, msg
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
    app.run(port=8080)
