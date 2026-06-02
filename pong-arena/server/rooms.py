import random
import string
import uuid
from game_state import GameState

rooms = {}

# --- MODIFICACIÓN FASE 1 ---
# Cambiamos el orden de la constante para que los dos primeros jugadores asuman los roles laterales
POSITIONS = [
    "LEFT",   # El Host (Jugador 1) estará a la izquierda
    "RIGHT",  # El primer invitado (Jugador 2) estará a la derecha
    "TOP",    # El segundo invitado (Jugador 3) estará arriba
    "BOTTOM"  # El tercer invitado (Jugador 4) estará abajo
]

def generate_room_code():
    # Genera un código aleatorio de 4 caracteres usando letras mayúsculas y dígitos
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

class Player:
    # Constructor para inicializar la sesión de un jugador
    def __init__(self, websocket, position):
        # Asignamos un identificador único universal (UUID) al jugador
        self.id = str(uuid.uuid4())
        # Almacenamos la referencia al socket de comunicación del jugador
        self.websocket = websocket
        # Asignamos la posición en el tablero (LEFT, RIGHT, TOP o BOTTOM)
        self.position = position
        # Bandera booleana para rastrear si el jugador está listo para iniciar
        self.ready = False
        # Usamos la posición como nombre predeterminado para mostrar en el lobby
        self.name = position

class Room:
    # Constructor para inicializar una nueva sala de juego
    def __init__(self):
        # Generamos y guardamos el código secreto único de esta sala
        self.code = generate_room_code()
        # Lista dinámica para almacenar los objetos Player conectados actualmente
        self.players = []
        # Definimos el límite de capacidad de la sala a 4 personas
        self.max_players = 4
        # Bandera booleana para rastrear si la partida ya comenzó
        self.started = False
        # Contador numérico de jugadores (opcional, puede calcularse con len(self.players))
        self.player_count = 0
        # Instanciamos el motor matemático autoritativo exclusivo de esta sala
        self.game_state = GameState()