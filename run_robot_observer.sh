#!/bin/bash

python start_observer.py --ip localhost --port 6666 --name observer &
python start_robot.py    --ip localhost --port 6666 --name terminator
