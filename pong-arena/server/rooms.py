import random
import string

from game_state import GameState

rooms = {}
POSITIONS = [
    "TOP",
    "RIGHT",
    "BOTTOM",
    "LEFT"
]

def generate_room_code():
    return ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=4
        )
    )

class Player:

    def __init__(self, websocket, position):

        self.websocket = websocket

        self.position = position

        self.ready = False

        self.name = "Anonymous"

class Room:

    def __init__(self):

        self.code = generate_room_code()

        self.players = []

        self.max_players = 4

        self.started = False

        self.player_count = 0

        self.game_state = GameState()