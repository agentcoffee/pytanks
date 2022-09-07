#!/bin/bash

python start_robot.py  --ip localhost --port 6666 --name terminator &
python start_player.py --ip localhost --port 6666 --name esteban
