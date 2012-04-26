#!/usr/bin/env sh
# Start the server for test_create_event.
python evite_test.py &

# Run the tests.
nosetests --verbosity=3
