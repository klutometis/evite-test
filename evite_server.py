from evite_test import Scheduler
from flask import Flask, request
import simplejson as json

app = Flask(__name__)
events = []

@app.route('/events', methods=['POST'])
def create_event():
    events.append(request.json)
    return json.dumps({'id': str(len(events) - 1)})

@app.route('/events/<int:id>')
def get_event(id):
    return json.dumps(events[id])

if __name__ == '__main__':
    app.run(debug=True,
            port=8080)
