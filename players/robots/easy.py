import time
import math
import random
from enum import Enum

from maths.vector import Vector
from maths.matrix import Matrix
from maths.matrix import RotationMatrix
from sprites.movable import Movable
from sprites.tank import TankState
from sprites.projectile import ProjectileSprite, ProjectileState
from sprites.explosion import ExplosionSprite, ExplosionState
from clients.type_enum import ClientType

import debug
from config.event_loop_time import EVENT_LOOP_TIME

from packets import *

class PlayerState(Enum):
    JOINING   = 1
    PLAYING   = 2
    TANK_DIED = 3
    EXIT      = 4

class Commands:
    def __init__(self, tank_uid):
        self.tank_uid = tank_uid

        self.go_sem    = 0
        self.stop_sem  = 0
        self.left_sem  = 0
        self.right_sem = 0
        self.shoot_sem = 0

        self.commands = []

    def get_commands(self):
        if self.go_sem == 1:
            self.__go_release()
        elif self.go_sem == 2:
            self.go_sem = 1

        if self.stop_sem == 1:
            self.__stop_release()
        elif self.stop_sem == 2:
            self.stop_sem = 1

        if self.left_sem == 1:
            self.__left_release()
        elif self.left_sem == 2:
            self.left_sem = 1

        if self.right_sem == 1:
            self.__right_release()
        elif self.right_sem == 2:
            self.right_sem = 1

        if self.shoot_sem == 1:
            self.__shoot_release()
        elif self.shoot_sem == 2:
            self.shoot_sem = 1

        t = self.commands
        self.commands = []
        return t

    def go(self):
        if self.go_sem == 0:
            self.commands.append(InputPacket(self.tank_uid,
                InputPacket.Key.UP, InputPacket.Event.PRESS))
        self.go_sem = 2

    def __go_release(self):
        self.commands.append(InputPacket(self.tank_uid,
            InputPacket.Key.UP, InputPacket.Event.RELEASE))
        self.go_sem = 0

    def stop(self):
        if self.down_sem == 0:
            self.commands.append(InputPacket(self.tank_uid,
                InputPacket.Key.DOWN, InputPacket.Event.PRESS))
        self.down_sem = 2

    def __stop_release(self):
        self.commands.append(InputPacket(self.tank_uid,
            InputPacket.Key.DOWN, InputPacket.Event.RELEASE))
        self.down_sem = 0

    def left(self):
        if self.left_sem == 0:
            self.commands.append(InputPacket(self.tank_uid,
                InputPacket.Key.LEFT, InputPacket.Event.PRESS))
        self.left_sem = 2

    def __left_release(self):
        self.commands.append(InputPacket(self.tank_uid,
            InputPacket.Key.LEFT, InputPacket.Event.RELEASE))
        self.left_sem = 0

    def right(self):
        if self.right_sem == 0:
            self.commands.append(InputPacket(self.tank_uid,
                InputPacket.Key.RIGHT, InputPacket.Event.PRESS))
        self.right_sem = 2

    def __right_release(self):
        self.commands.append(InputPacket(self.tank_uid,
            InputPacket.Key.RIGHT, InputPacket.Event.RELEASE))
        self.right_sem = 0

    def shoot(self):
        if self.shoot_sem == 0:
            self.commands.append(InputPacket(self.tank_uid,
                InputPacket.Key.SPACE, InputPacket.Event.PRESS))
        self.shoot_sem = 2

    def __shoot_release(self):
        self.commands.append(InputPacket(self.tank_uid,
            InputPacket.Key.SPACE, InputPacket.Event.RELEASE))
        self.shoot_sem = 0

class EasyRobot:
    def __init__(self, connection, tank_name):
        # Game init
        self.connection = connection
        self.state      = PlayerState.JOINING
        self.tank_name  = tank_name
        self.target     = "esteban"
        self.shoot_timeout = 0
 
        print("Sent Initial JoinReq, Listening ...")
        self.connection.put( JoinReqPacket(ClientType.TANK) )

        packet = self.connection.blocking_get()

        if type(packet) == JoinAckPacket:
            self.field = packet.field
        else:
            raise Exception("Expected JoinAck, got {}".format(type(packet)))

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
        commands     = None

        __run_start        = (time.monotonic_ns() / 1000000)
        __idle_total       = 0
        __round_number     = 0

        # TODO implement sync interval, dont hog CPU
        while True:
            __t         = (time.monotonic_ns() / 1000000)
            deadline    = __t + EVENT_LOOP_TIME
            __run_total = __t - __run_start

            if self.state is PlayerState.JOINING:
                print("Sent JoinReq, Listening ...")
                self.connection.put( CreateTankPacket(self.tank_name) )

                if self.connection.poll():
                    packet = self.connection.get()

                    if type(packet) == TankAckPacket:
                        self.state    = PlayerState.PLAYING
                        self.tank_uid = packet.uid
                        commands      = Commands(self.tank_uid)

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

                        self.robot_compute(states_list, commands)

                        for m in commands.get_commands():
                            self.connection.put(m)

                    elif type(packet) is TankDiedPacket:
                        self.state = PlayerState.TANK_DIED

            elif self.state is PlayerState.TANK_DIED:
                print("You died.")
                self.state = PlayerState.EXIT

            elif self.state is PlayerState.EXIT:
                print("Disconnecting from the server")
                self.connection.put( LeavePacket(self.tank_uid) )
                return

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

    def robot_compute(self, states_list, commands):
        for s in states_list:
            if type(s) is TankState and s.name == self.tank_name:
                me = s

            if type(s) is TankState and s.name == self.target:
                target = s

        try:
            shoot_line = target.position - me.position
            shoot_line_norm  = shoot_line.normalize()
            shoot_line_angle = math.asin(shoot_line_norm.y)

            if shoot_line.x < 0:
                if shoot_line.y > 0:
                    # 2. Quartal
                    shoot_line_angle = math.pi - shoot_line_angle
                else:
                    # 3. Quartal
                    shoot_line_angle = math.pi - shoot_line_angle
            else:
                if shoot_line.y > 0:
                    # 1. Quartal
                    pass
                else:
                    # 4. Quartal
                    shoot_line_angle = 2*math.pi + shoot_line_angle

            angle_diff = shoot_line_angle - me.angle

            if angle_diff > math.pi:
                angle_diff = -(2*math.pi - angle_diff)
            elif angle_diff < -math.pi:
                angle_diff =  (2*math.pi + angle_diff)

            if -0.1 < angle_diff < 0.1:
                if (time.time() - self.shoot_timeout) > 5:
                    self.shoot_timeout = time.time()
                    commands.shoot()
            elif angle_diff > 0:
                commands.right()
            else:
                commands.left()

            if shoot_line.length() > 100:
                commands.go()

        except UnboundLocalError as e:
            print(e)
            pass

        except ZeroDivisionError as e:
            print(e)
            pass
