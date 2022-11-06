from Xlib import X, threaded

import logging
from engine.maths.vector import Vector

from engine.objects.generics.drawable import Drawable
from engine.objects.sprites.field import FieldObject
from engine.objects.sprites.tank import TankObject

# Used to communicate the state to the clients
class LeaderboardState:
    def __init__(self, uid, board=None, position=None):
        self.position = position
        self.board    = board
        self.uid      = uid

    def get_state(self):
        return LeaderboardState(self.uid, self.board, self.position)

    def set_state(self, leaderboard_state):
        assert(type(leaderboard_state) == LeaderboardState)
        self.position = leaderboard_state.position
        self.board    = leaderboard_state.board
        self.uid      = leaderboard_state.uid

class LeaderboardSprite(Drawable):
    def __init__(self, screen, window, gc, leaderboard_state):
        # Init the drawable context
        Drawable.__init__(self, screen, window, gc)

        # Init the state
        self.state = leaderboard_state

        logging.info(f"Instantiated Leaderboard")

    def __str__(self):
        return "LeaderboardSprite: " + str(self.state.uid)

    def draw_leaderboard(self, fg_border, fg_font):
        offset = 0
        self.state.board.sort(key=lambda x : x[1], reverse=True)
        if self.state.board is not None and self.state.position is not None:
            for name, health in self.state.board:
                self.gc.change(foreground = fg_font)
                self.window.draw_text(self.gc,
                                      int(self.state.position.x),
                                      int(self.state.position.y + 15*offset),
                                      f"{name} : {health}")
                offset += 1

    def draw(self):
        self.draw_leaderboard(self.screen.black_pixel, self.red)

    def erase(self):
        self.draw_leaderboard(self.screen.white_pixel, self.screen.white_pixel)

class LeaderboardObject:
    def __init__(self, leaderboard_state, id_generator):
        # Init the state
        self.state = leaderboard_state
        self.id_generator = id_generator

        logging.info(f"Instantiated Leaderboard {self.state.uid}")

    def __str__(self):
        return "Leaderboard: " + str(self.state.uid)

    def step(self, objects, movables):
        for o in objects:
            if isinstance(o, FieldObject):
                self.state.position = Vector(o.state.x_sup + 10, o.state.y_inf + 10)
                break

        self.state.board = []
        for t in movables:
            if isinstance(t, TankObject):
                self.state.board.append((t.state.name, t.state.health))
