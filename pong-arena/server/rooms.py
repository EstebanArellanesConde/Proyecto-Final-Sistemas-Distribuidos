# Importamos la librería random para generar selecciones aleatorias (para el código de sala)
import random
# Importamos string para obtener constantes de caracteres (letras y números)
import string
# Importamos uuid para generar identificadores únicos universales para cada jugador
import uuid

# Importamos el motor matemático y de estado del juego
from game_state import GameState

# Diccionario global en memoria para almacenar todas las salas activas usando su código como llave
rooms = {}

# Lista constante que define el orden estricto de asignación de posiciones en el tablero
POSITIONS = [
    "LEFT",   # El Host (Jugador 1) siempre estará a la izquierda
    "RIGHT",  # El primer invitado (Jugador 2) siempre estará a la derecha
    "TOP",    # El segundo invitado (Jugador 3) tomará la parte superior
    "BOTTOM"  # El tercer invitado (Jugador 4) tomará la parte inferior
]

# Diccionario constante para asignar un color hexadecimal específico a cada posición del tablero
COLORS = {
    "LEFT": "#ff0000",   # Rojo puro para el Jugador 1 (Izquierda)
    "RIGHT": "#000080",  # Azul marino para el Jugador 2 (Derecha)
    "TOP": "#ffff00",    # Amarillo puro para el Jugador 3 (Arriba)
    "BOTTOM": "#008000"  # Verde puro para el Jugador 4 (Abajo)
}

# Función para generar un código secreto y único para invitar jugadores
def generate_room_code():
    # Retorna una cadena de 4 caracteres aleatorios combinando letras mayúsculas y dígitos
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# Clase que representa la sesión y estado individual de un cliente conectado
class Player:
    
    # Constructor que inicializa los datos de red y estado visual del jugador
    def __init__(self, websocket, position):
        # Generamos un ID único para evitar colisiones en la memoria
        self.id = str(uuid.uuid4())
        # Guardamos la tubería de comunicación abierta con este cliente
        self.websocket = websocket
        # Asignamos su posición física en el tablero (LEFT, RIGHT, etc.)
        self.position = position
        # Inicializamos su estado de preparación en falso
        self.ready = False
        # Usamos su posición como nombre a mostrar temporalmente en el UI
        self.name = position
        # Asignamos el color visual correspondiente consultando el diccionario global COLORS
        self.color = COLORS[position]

# Clase que encapsula todo el ecosistema de una partida específica
class Room:
    
    # Constructor que inicializa la sala, ahora permitiendo configurar capacidad y puntaje
    def __init__(self, max_players=4, target_score=10):
        # Generamos el código de 4 letras para unirse a esta sala
        self.code = generate_room_code()
        # Inicializamos la lista vacía de jugadores participantes
        self.players = []
        # Guardamos el límite de jugadores permitido para esta instancia (2 o 4)
        self.max_players = max_players
        # Guardamos el límite de puntos necesarios para ganar la ronda
        self.target_score = target_score
        # Bandera de control para saber si la partida ya está en curso
        self.started = False
        
        # Instanciamos el motor físico inyectando el puntaje objetivo establecido por el Host
        self.game_state = GameState(target_score)