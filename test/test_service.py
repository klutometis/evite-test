import unittest
import sys
import time
import httplib2
import simplejson as json

from evite_test import Scheduler, Server

ENDPOINT = 'http://localhost:8080/events'

@unittest.skip('because')
def test_create_event():
    h = httplib2.Http('.cache')

    event = {
        'msg': 'This is a test event',
        'recipients': [
            'josh.frederick@evite.com',
            'jessica.stanton@evite.com',
            'warren.runk@evite.com',
        ],
        'start': time.time(),
        'repeat': 10,  # how many times to send the event
        'interval': 1, # how many seconds between sends
    }
    event_json = json.dumps(event)
    resp, content = h.request(
        ENDPOINT,
        'POST',
        body=event_json, 
        headers={'content-type':'application/json'}
    )
    
    # make sure we got a 200
    assert resp.status == 200, "Status (%d) was not 200 (success)" % resp.status
    
    # make sure an ID is returned in the resp
    resp_json = json.loads(content)
    assert 'id' in resp_json, "id was not returned in the create response"

    # retrieve the event we just created
    resp, content = h.request(
         ENDPOINT + '/' + resp_json['id'],
        'GET',
    )
    assert resp.status == 200

    # make sure all the fields are present and updated
    saved_event = json.loads(content)
    for field in ['msg', 'recipients', 'start', 'repeat', 'interval']:
        assert event[field] == saved_event[field], \
            "The retrieved %s did not match" % field


@unittest.skip('nope')
def test_scheduler():
    sent_msgs = {}
    def sender(rcpt, msg):
        if rcpt not in sent_msgs:
            sent_msgs[rcpt] = []
        sent_msgs[rcpt].append((msg, time.time()))

    scheduler = Scheduler(sender)
    scheduler.add_event(**{
        'msg': 'This is a test event',
        'recipients': [
            'josh.frederick@evite.com',
            'jessica.stanton@evite.com',
            'warren.runk@evite.com',
        ],
        'start': time.time(),
        'repeat': 3,  # how many times to send the event
        'interval': 1, # how many seconds between sends
    })

    # ensure that we haven't sent any until we start the scheduler
    assert not sent_msgs

    scheduler.start()
    time.sleep(5)
    scheduler.stop()
    
    assert len(sent_msgs) == 3, "We have messages for different recipients"
    for rcpt in [
            'josh.frederick@evite.com',
            'jessica.stanton@evite.com',
            'warren.runk@evite.com',
        ]:
        assert len(sent_msgs[rcpt]) == 3, \
            "number of msgs was %d" % len(sent_msgs[rcpt])
        last_msg = None
        for msg in sent_msgs[rcpt]:
            assert msg
            if last_msg:
                assert msg[1] - last_msg[1] > 1
            last_msg = msg

@unittest.skip('nope')
def test_scheduler_overlap():
    sent_msgs = {}
    def sender(rcpt, msg):
        if msg not in sent_msgs:
            sent_msgs[msg] = []
        assert rcpt == 'josh.frederick@evite.com'
        sent_msgs[msg].append(time.time())

    scheduler = Scheduler(sender)
    scheduler.add_event(**{
        'msg': 'This is a two sec repeat',
        'recipients': [
            'josh.frederick@evite.com',
        ],
        'start': time.time(),
        'repeat': 2,  # how many times to send the event
        'interval': 2, # how many seconds between sends
    })
    scheduler.add_event(**{
        'msg': 'This is a one sec repeat',
        'recipients': [
            'josh.frederick@evite.com',
        ],
        'start': time.time(),
        'repeat': 3,  # how many times to send the event
        'interval': 1, # how many seconds between sends
    })

    # ensure that we haven't sent any until we start the scheduler
    assert not sent_msgs
    

    scheduler.start()
    time.sleep(4)
    scheduler.stop()
    
    assert len(sent_msgs) == 2
    assert len(sent_msgs['This is a two sec repeat']) == 2
    assert len(sent_msgs['This is a one sec repeat']) == 3

def test_integration():
    h = httplib2.Http('.cache')
    sent_msgs = {}
    def sender(rcpt, msg):
        print >> sys.stderr, id(sent_msgs)
        # print >> sys.stderr, rcpt, msg, sent_msgs
        if rcpt not in sent_msgs:
            sent_msgs[rcpt] = []
        sent_msgs[rcpt].append((msg, time.time()))
    
    # print >> sys.stderr, 'test_integration/sender', id(sender), dir(sender), sender.func_closure, sender.func_globals, sender.func_dict
    print >> sys.stderr, 'test_integration/sender', id(sender)
    port = 9091
    server = Server(sender, port)
    server.start()

    event = {
        'msg': 'This is a test event',
        'recipients': [
            'josh.frederick@evite.com',
            'jessica.stanton@evite.com',
            'warren.runk@evite.com',
        ],
        'start': time.time(),
        'repeat': 3,  # how many times to send the event
        'interval': 1, # how many seconds between sends
    }
    event_json = json.dumps(event)
    resp, content = h.request(
        'http://localhost:%d/events' % port,
        'POST',
        body=event_json, 
        headers={'content-type':'application/json'}
    )
    
    # ensure that we haven't sent any until we start the scheduler
    assert not sent_msgs

    # make sure we got a 200
    assert resp.status == 200, "Status (%d) was not 200 (success)" % resp.status
    time.sleep(5)
    server.stop()

    print >> sys.stderr, id(sent_msgs)
    print >> sys.stderr, sent_msgs, dir()
    assert len(sent_msgs) == 3, "We have messages for different recipients"
    for rcpt in [
            'josh.frederick@evite.com',
            'jessica.stanton@evite.com',
            'warren.runk@evite.com',
        ]:
        assert len(sent_msgs[rcpt]) == 3, \
            "number of msgs was %d" % len(sent_msgs[rcpt])
        last_msg = None
        for msg in sent_msgs[rcpt]:
            assert msg
            if last_msg:
                assert msg[1] - last_msg[1] > 1
            last_msg = msg



if __name__ == '__main__':
    unittest.main()
