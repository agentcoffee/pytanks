import time
import math
import random
from Xlib import X, display, threaded
from enum import Enum

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.movable import Movable
from sprites.tank import TankSprite, TankState
from sprites.projectile import ProjectileSprite, ProjectileState
from sprites.explosion import ExplosionSprite, ExplosionState

import debug
from config.event_loop_time import EVENT_LOOP_TIME

from packets import *

class PlayerState(Enum):
    JOINING   = 1
    PLAYING   = 2
    TANK_DIED = 3
    EXIT      = 4

class EasyRobot:
    def __init__(self, display, connection, tank_name):
        # Game init
        self.connection = connection
        self.state      = PlayerState.JOINING

        # X11 init
        self.display        = display
        self.tank_name      = tank_name
 
        print("Sent Initial JoinReq, Listening ...")
        self.connection.put( JoinReqPacket(self.tank_name) )

        packet = self.connection.blocking_get()

        if type(packet) == JoinAckPacket:
            self.state    = PlayerState.PLAYING
            self.tank_uid = packet.uid
            self.field    = packet.field
        else:
            raise Exception("Expected JoinAck, got {}".format(type(packet)))

        self.screen = self.display.screen()
        self.window = self.screen.root.create_window(
            10, 10, self.field.width, self.field.height, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.KeyReleaseMask,
            )
        self.gc = self.window.create_gc(
            foreground = self.screen.black_pixel,
            background = self.screen.white_pixel,
            )
 
        self.window.map()

    def loop(self):
        try:
            self._loop()
        finally:
            print("Cleaning up")
            self.connection.close()
 
    def _loop(self):
        ROLLING_AVERAGE_SIZE = 5

        objects      = {}
        round_number = 0
        latency_map  = {}

        __run_start        = (time.monotonic_ns() / 1000000)
        __idle_total       = 0
        __round_number     = 0
        __update_intervals = [0] * ROLLING_AVERAGE_SIZE
        __update_timestamp = 0

        e = self.display.next_event()

        if e.type != X.Expose:
            print("Need an expose event first.")

        # TODO implement sync interval, dont hog CPU
        while True:
            __t         = (time.monotonic_ns() / 1000000)
            deadline    = __t + EVENT_LOOP_TIME
            __run_total = __t - __run_start

            self.display.sync()

            if self.state is PlayerState.JOINING:
                print("Sent JoinReq, Listening ...")
                self.connection.put( JoinReqPacket(self.tank_name) )

                if self.connection.poll():
                    packet = self.connection.get()

                    if type(packet) == JoinAckPacket():
                        self.state    = PlayerState.PLAYING
                        self.tank_uid = packet.uid
                        self.field    = packet.field

            elif self.state is PlayerState.PLAYING:
                # Get the lates state packet
                packet = None

                try:
                    while True:
                        packet = self.connection.get()
                except BlockingIOError:
                    pass

                if packet is not None:
                    if type(packet) is StatePacket:
                        round_number = packet.round_nr
                        states_list  = packet.game_state
                        cmd_id_list  = packet.cmd_id_list

                        responses = self.robot_compute(states_list)

                        for m in responses:
                            self.connection.put(m)

                    elif type(packet) is TankDiedPacket:
                        self.state = PlayerState.TANK_DIED

            elif self.state is PlayerState.TANK_DIED:
                print("You died.")

            elif self.state is PlayerState.EXIT:
                print("Disconnecting from the server")
                self.connection.put( LeavePacket(self.tank_uid) )
                return

            # draw game border
            self.gc.change(foreground = self.screen.black_pixel)
            self.window.rectangle(self.gc, 0, 0,
                    int(self.field.width), int(self.field.height))

            round_number += 1

            __idle_start = (time.monotonic_ns() / 1000000)

            if __idle_start > deadline:
                print("Missed round " + str(__round_number) + " by: " +
                        str(__idle_start - deadline))

            if (__round_number % 100) == 0:
                latency_map = {uid:timestamp for (uid, timestamp) in latency_map.items()
                        if timestamp > __t + 100}

            # Coarse grained waiting
            while ( deadline - (time.monotonic_ns() / 1000000) ) > (EVENT_LOOP_TIME / 5) :
                time.sleep( EVENT_LOOP_TIME / (5 * 1000) )

            # Fine grained waiting
            while time.monotonic_ns() / 1000000 < deadline:
                continue

            __idle_total   += (time.monotonic_ns() / 1000000) - __idle_start
            __round_number += 1

    def robot_compute(self, states_list):
        print(states_list)
        return []
