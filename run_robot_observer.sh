#!/bin/bash

python start_observer.py --ip localhost --port 6667 --name observer &
python start_robot.py    --ip localhost --port 6667 --name terminator
