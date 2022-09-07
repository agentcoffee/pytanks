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
from clients.type_enum import ClientType

import debug
from config.event_loop_time import EVENT_LOOP_TIME

from packets import *

class ObserverState(Enum):
    JOINING   = 1
    OBSERVING = 2
    EXIT      = 3

class Observer:
    def __init__(self, display, connection, name):
        # Game init
        self.connection = connection
        self.state      = ObserverState.JOINING
        # X11 init
        self.display    = display
 
        print("Sent Initial JoinReq, Listening ...")
        self.connection.put( JoinReqPacket(ClientType.OBSERVER) )

        packet = self.connection.blocking_get()

        if type(packet) == JoinAckPacket:
            self.field = packet.field
        else:
            raise Exception("Expected JoinAck, got {}".format(type(packet)))
        self.state = ObserverState.OBSERVING

        self.screen = self.display.screen()
        self.window = self.screen.root.create_window(
            10, 10, self.field.width, self.field.height, 1,
            self.screen.root_depth,
            background_pixel=self.screen.white_pixel,
            event_mask=X.ExposureMask | X.KeyPressMask | X.KeyReleaseMask )
        self.gc = self.window.create_gc(
            foreground = self.screen.black_pixel,
            background = self.screen.white_pixel )
 
        self.window.map()

    def autoRepeatDetection(self):
        events = []

        i = self.display.pending_events()
        while i > 0:
            e = self.display.next_event()
            i -= 1

            if i >= 1 and e.type == X.KeyRelease:
                f = self.display.next_event()
                i -= 1
                if f.type != X.KeyPress or e.detail != f.detail:
                    events.insert(0, e)
                    events.insert(0, f)
            else:
                events.insert(0, e)
        return events

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

        __run_start        = (time.monotonic_ns() / 1000000)
        __idle_total       = 0
        __round_number     = 0

        e = self.display.next_event()

        if e.type != X.Expose:
            print("Need an expose event first.")

        # TODO implement sync interval, dont hog CPU
        while True:
            __t         = (time.monotonic_ns() / 1000000)
            deadline    = __t + EVENT_LOOP_TIME
            __run_total = __t - __run_start

            self.display.sync()

            if self.state is ObserverState.OBSERVING:
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

                        for state in states_list:
                            if state.uid in objects:
                                objects[state.uid].erase()
                                objects[state.uid].setState(state)
                            else:
                                if   type(state) is TankState:
                                    objects[state.uid] = TankSprite(
                                        self.screen, self.window, self.gc, state)
                                elif type(state) is ProjectileState:
                                    objects[state.uid] = ProjectileSprite(
                                        self.screen, self.window, self.gc, state)
                                elif type(state) is ExplosionState:
                                    objects[state.uid] = ExplosionSprite(
                                        self.screen, self.window, self.gc, state)
                                else:
                                    raise NotImplementedError(type(state))
                            objects[state.uid].draw()

                        # TODO not very performant
                        uid_list      = [s.uid for s in states_list]
                        orphaned_uids = []
                        # Clean orphaned objects
                        for uid in objects:
                            if uid not in uid_list:
                                objects[uid].erase()
                                orphaned_uids.append(uid)

                        for uid in orphaned_uids:
                            del objects[uid]

            elif self.state is ObserverState.EXIT:
                print("Disconnecting from the server")
                self.connection.put( LeavePacket(0) )
                return

            # draw game border
            self.gc.change(foreground = self.screen.black_pixel)
            self.window.rectangle(self.gc, 0, 0,
                    int(self.field.width), int(self.field.height))
            
            # Then X11 events
            for e in self.autoRepeatDetection():
                if e.type == X.Expose:
                    for o in objects.values():
                        o.draw()
                elif e.type == X.KeyPress or e.type == X.KeyRelease:
                    if e.detail == 9 or e.detail == 66: # ESC
                        self.state = ObserverState.EXIT

            round_number += 1

            __idle_start = (time.monotonic_ns() / 1000000)

            if __idle_start > deadline:
                print("Missed round " + str(__round_number) + " by: " +
                        str(__idle_start - deadline))

            # Coarse grained waiting
            while ( deadline - (time.monotonic_ns() / 1000000) ) > (EVENT_LOOP_TIME / 5) :
                time.sleep( EVENT_LOOP_TIME / (5 * 1000) )

            # Fine grained waiting
            while time.monotonic_ns() / 1000000 < deadline:
                continue

            __idle_total   += (time.monotonic_ns() / 1000000) - __idle_start
            __round_number += 1
