import simplejson as json
from time import time, sleep
from threading import Timer, Thread
from flask import Flask, request
from multiprocessing import Process, Queue

app = Flask(__name__)
events = None
queue = None

def init_app():
    """Initialize the events-list and queue."""
    global events, queue
    queue = Queue()
    events = []

@app.route('/events', methods=['POST'])
def create_event():
    """Add an event to the events list so as to assign it an id; put
    the event in the queue so that the sender picks it up."""
    global events, queue
    event = request.json
    events.append(event)
    # Should we make this non-blocking?
    queue.put(event)
    return json.dumps({'id': str(len(events) - 1)})

@app.route('/events/<int:id>')
def get_event(id):
    """Read an event from the events list by id."""
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
        """Read blockingly from the event queue, adding events for
        immediate dispatch to the scheduler.

        NB: If the server is restarted, this thread will block in
        perpetuity."""
        event = queue.get()
        self.scheduler.add_event(immediate=True, **event)
        self.send_from_queue()

    def start(self):
        """Initialize the app; start the flask server in a process;
        start the sender-thread that reads from the queue."""
        init_app()
        self.server = Process(target=app.run,
                              kwargs={'port': self.port})
        self.server.start()

        # Wait for server to start
        sleep(1)

        # Start thread that monitors the queue and sends when we get
        # new events.
        send_from_queue = Thread(target=self.send_from_queue)
        send_from_queue.daemon = True
        send_from_queue.start()

    def stop(self):
        """Stop the server.

        NB: This does not reap the sender-thread that reads from the
        queue."""
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
        """Start the messages in the queue."""
        for message in self.messages:
            message.start()

    def stop(self):
        """Stop the currently executing messages."""
        for message in self.messages:
            message.cancel()

if __name__ == '__main__':
    init_app()
    app.run(port=8080)
