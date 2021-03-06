import time
import math
import random
from Xlib import X, display, threaded

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.movable import Movable
from sprites.tank import TankSprite, TankState
from sprites.projectile import ProjectileSprite, ProjectileState
from sprites.explosion import ExplosionSprite, ExplosionState

import debug
from event_loop_time import EVENT_LOOP_TIME

from packets import *


class Window:
    def __init__(self, display, gameloop_pipe, tank_name):
        # Game init
        self.gameloop_pipe = gameloop_pipe
        self.gameloop_pipe.send( JoinReqPacket(tank_name) )
        print("Sent JoinReq, Listening ...")

        packet = self.gameloop_pipe.blocking_recv()
        print("Caught packet")
        if type(packet) is not JoinAckPacket:
            raise Exception("Received garbage on connection accept")

        self.tank_uid = packet.uid
        self.field    = packet.field

        # X11 init
        self.display        = display
        self.tank_name      = tank_name
 
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
                # end if
            else:
                events.insert(0, e)
            # end if
        return events

    def loop(self):
        try:
            self._loop()
        finally:
            print("Cleaning up")
            self.gameloop_pipe.close()
 
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

            # Create new, update existing objects
            #if self.gameloop_pipe.poll():
            packet = None
            try:
                packet = self.gameloop_pipe.recv_latest()
                assert(type(packet) == StatePacket)
            except BlockingIOError:
                pass

            if packet is not None:
                round_number = packet.round_nr
                states_list  = packet.game_state
                cmd_id_list  = packet.cmd_id_list

                #for c, t in latency_map.items():
                for c in cmd_id_list:
                    if c in latency_map.keys():
                        __t = (time.monotonic_ns() / 1000000)
                        debug.latency("Client received response to Input: {} at {}"
                                .format(c, __t))
                        try:
                            print("Latency: " + str(__t - latency_map[c]))
                        except KeyError:
                            print("OOOPS: Latency > 100ms, deleted key before response came!")
                        del latency_map[c]

                for state in states_list:
                    if state.uid in objects:
                        objects[state.uid].erase()
                        objects[state.uid].setState(state)
                    else:
                        if   type(state) is TankState:
                            objects[state.uid] = TankSprite(
                                self.screen, self.window, self.gc,
                                state)
                        elif type(state) is ProjectileState:
                            objects[state.uid] = ProjectileSprite(
                                self.screen, self.window, self.gc,
                                state)
                        elif type(state) is ExplosionState:
                            objects[state.uid] = ExplosionSprite(
                                self.screen, self.window, self.gc,
                                state)
                        else:
                            raise NotImplementedError(type(state))
                        # end if
                    # end if
                    objects[state.uid].draw()
                # end for

                # TODO not very performant
                uid_list      = [s.uid for s in states_list]
                orphaned_uids = []
                # Clean orphaned objects
                for uid in objects:
                    if uid not in uid_list:
                        objects[uid].erase()
                        orphaned_uids.append(uid)
                    # end if
                # end for
                for uid in orphaned_uids:
                    del objects[uid]
            # end if

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
                        raise SystemExit
                    else:
                        try:
                            cmd_id = hex(random.randint(0, 2**16))
                            t = (time.monotonic_ns() / 1000000)
                            latency_map[cmd_id] = t
                            packet = InputPacket(self.tank_uid, e, cmd_id, t)
                            self.gameloop_pipe.send( packet )
                            if packet.event == InputPacket.Event.PRESS:
                                debug.input("> " + str(packet.key.name))
                            if packet.event == InputPacket.Event.RELEASE:
                                debug.input("< " + str(packet.key.name))
                            debug.latency("Client sent Input: {} at {}".format(cmd_id, t))
                        except KeyError:
                            pass
                # end if
            # end for

            round_number += 1

            __idle_start = (time.monotonic_ns() / 1000000)

            if __idle_start > deadline:
                print("Missed round " + str(__round_number) + " by: " +
                        str(__idle_start - deadline))

            # Ez debugging
            if (__round_number % 100) == 0:
                # Clean the latency_map of orphaned entries,
                #   remove after we haven't received a response for 100 ms.
                latency_map = {uid:timestamp for (uid, timestamp) in latency_map.items()
                        if timestamp > __t + 100}

            # Coarse grained waiting
            while ( deadline - (time.monotonic_ns() / 1000000) ) > (EVENT_LOOP_TIME / 5) :
                time.sleep( EVENT_LOOP_TIME / (5 * 1000) )
            # end while

            # Fine grained waiting
            while time.monotonic_ns() / 1000000 < deadline:
                continue
            # end while

            __idle_total   += (time.monotonic_ns() / 1000000) - __idle_start
            __round_number += 1
        # end while
