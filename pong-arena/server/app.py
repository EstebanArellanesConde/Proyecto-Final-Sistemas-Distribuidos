# Importamos asyncio para manejar la concurrencia y los bucles de tiempo real sin bloquear el hilo principal
import asyncio
# Importamos los componentes principales de FastAPI para levantar el servidor y manejar la API
from fastapi import FastAPI
# Importamos la clase WebSocket para tipar y manejar las conexiones bidireccionales
from fastapi import WebSocket
# Importamos la excepción específica para detectar cuando un cliente pierde la conexión de red
from fastapi import WebSocketDisconnect
# Importamos HTMLResponse para devolver la vista principal del juego desde el servidor
from fastapi.responses import HTMLResponse
# Importamos StaticFiles para poder servir el archivo game.js y otros estáticos sin procesar
from fastapi.staticfiles import StaticFiles
# Importamos Jinja2Templates para renderizar dinámicamente el archivo index.html
from fastapi.templating import Jinja2Templates
# Importamos Request, necesario para que Jinja2 pueda procesar el contexto de la petición web
from fastapi import Request

# Importamos las clases y estructuras de datos para gestionar las salas desde nuestro módulo local
from rooms import Room
from rooms import rooms
from rooms import Player
from rooms import POSITIONS

# Instanciamos la aplicación principal de FastAPI que actuará como nuestro servidor
app = FastAPI()

# Montamos el directorio "static" en la ruta "/static" para que el navegador pueda descargar game.js
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# Configuramos el motor de plantillas apuntando a la carpeta "templates" donde vive index.html
templates = Jinja2Templates(
    directory="templates"
)

# Definimos la ruta raíz ("/") por método GET para servir la interfaz web del cliente
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Retornamos la plantilla HTML renderizada, pasando la petición actual como contexto
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

# Función asíncrona para notificar a todos los clientes de una sala sobre los jugadores conectados
async def broadcast_room_status(room):
    # Construimos el diccionario con la estructura de estado actual de la sala
    data = {
        "type": "room_status",
        "players": len(room.players), # Cantidad actual de jugadores conectados
        # Compresión de lista para extraer los datos públicos de cada jugador en la sala
        "players": [
            {
                "name": player.name,
                "position": player.position,
                "ready": player.ready
            }
            for player in room.players
        ],
        "max_players": room.max_players # Límite máximo de la sala (4)
    }

    # Lista temporal para almacenar referencias a clientes que hayan perdido conexión
    disconnected = []

    # Iteramos sobre todos los jugadores actualmente registrados en la memoria de la sala
    for player in room.players:
        # Bloque de captura de errores para intentar enviar el mensaje de forma segura
        try:
            # Enviamos el diccionario serializado a JSON a través de la tubería WebSocket
            await player.websocket.send_json(data)
        # Si ocurre cualquier error de red durante el envío...
        except Exception:
            # Añadimos al jugador a la lista de desconectados para limpiarlo posteriormente
            disconnected.append(player)

    # Iteramos sobre los jugadores que fallaron en recibir el mensaje
    for player in disconnected:
        # Verificamos por seguridad que el jugador siga existiendo en la lista de la sala
        if player in room.players:
            # Removemos al jugador caído de la lista activa para liberar el espacio
            room.players.remove(player)

# Función asíncrona central para procesar cualquier mensaje entrante de un cliente
async def handle_message(player, room, message):
    # Si el cliente indica que está listo para jugar...
    if message["type"] == "ready":
        # Actualizamos el estado interno del jugador a verdadero
        player.ready = True
        # Notificamos a toda la sala del cambio para que la UI de la lista se actualice
        await broadcast_room_status(room)
        
        # --- NUEVA LÓGICA DE INICIO DE PARTIDA FASE 1 ---
        # Verificamos si la cantidad actual de jugadores en la sala es exactamente 2 o 4
        if len(room.players) in [2, 4]:
            # Comprobamos si todos y cada uno de los jugadores en la sala tienen su estado 'ready' en True
            all_ready = all(p.ready for p in room.players)
            
            # Si todos están listos y la partida no ha comenzado previamente en el motor...
            if all_ready and not room.game_state.started:
                # Inyectamos la cantidad de jugadores activos para que el motor habilite físicas 2p o 4p
                room.game_state.start_game(len(room.players))
                
                # Preparamos un mensaje de red para ordenar a los clientes que cambien de pantalla
                start_data = {"type": "game_start"}
                
                # Iteramos sobre todos los jugadores conectados a la sala
                for p in room.players:
                    try:
                        # Despachamos la orden de inicio a través del socket de cada cliente
                        await p.websocket.send_json(start_data)
                    except:
                        # Ignoramos silenciosamente si un cliente falló en este microsegundo
                        pass
        
    # Si el mensaje es un evento de teclado (input) capturado en el frontend...
    elif message["type"] == "input":
        # Extraemos la instancia única de físicas (GameState) de esta sala
        game = room.game_state
        # Actualizamos el estado de la tecla en el servidor pasando la posición y el booleano
        game.set_input(player.position, message["key"], message["pressed"])

# Función asíncrona que empaqueta y transmite las coordenadas matemáticas a todos los clientes
async def broadcast_game_state(room):
    # Extraemos el motor de juego activo
    game = room.game_state
    
    # Preparamos el payload con las posiciones absolutas calculadas en este fotograma
    data = {
        "type": "game_state",
        "ball_x": game.ball_x, # Coordenada horizontal de la pelota
        "ball_y": game.ball_y, # Coordenada vertical de la pelota
        "paddles": game.paddles, # Diccionario completo con las posiciones de las paletas
        "active_players": game.active_players # Cantidad de jugadores para condicionales visuales en UI
    }

    # Iteramos sobre los jugadores conectados para transmitirles el estado
    for player in room.players:
        try:
            # Enviamos el estado del juego serializado
            await player.websocket.send_json(data)
        # Si un jugador se desconecta en medio del fotograma, lo ignoramos silenciosamente
        except:
            pass

# Bucle asíncrono infinito que mantiene vivo el motor de físicas de una partida
async def game_loop(room):
    # Ciclo de vida principal del servidor para esta sala
    while True:
        # Obtenemos la referencia al estado del juego
        game = room.game_state
        # Ejecutamos el ciclo matemático (físicas, movimientos, colisiones)
        game.update()
        # Transmitimos el nuevo estado recalculado a todos los jugadores
        await broadcast_game_state(room)
        # Pausamos la corrutina por 1/60 de segundo para forzar un refresco de 60 Fotogramas Por Segundo (FPS)
        await asyncio.sleep(1/60)

# Endpoint WebSocket exclusivo para el jugador creador (Host)
@app.websocket("/host")
async def host_room(websocket: WebSocket):
    # Aceptamos el protocolo de conexión ("handshake") del cliente
    await websocket.accept()
    # Instanciamos una nueva sala completamente limpia
    room = Room()
    # Guardamos la sala en el diccionario global del servidor usando su código como llave
    rooms[room.code] = room

    # Desatamos el bucle de juego en una tarea en segundo plano para no bloquear este endpoint
    asyncio.create_task(
        game_loop(room)
    )

    # Creamos el objeto jugador para el Host, asignándole automáticamente la posición inicial (LEFT)
    player = Player(
        websocket,
        POSITIONS[0]
    )
    # Agregamos al Host a la lista de jugadores de su propia sala
    room.players.append(player)

    # Notificamos el estado inicial de la sala (solo está él de momento)
    await broadcast_room_status(room)

    # Le enviamos un mensaje privado confirmando el código secreto de la sala recién creada
    await websocket.send_json({
        "type": "room_created",
        "code": room.code
    })

    # Iniciamos el bucle de escucha para atrapar todos los comandos que envíe este cliente
    try:
        import json # Importación local para procesar los payloads
        while True:
            # Pausamos la ejecución hasta recibir un texto plano desde el socket
            raw = await websocket.receive_text()
            # Convertimos el JSON de texto a un diccionario Python
            message = json.loads(raw)
            # Delegamos el mensaje procesado al enrutador central
            await handle_message(
                player,
                room,
                message
            )
    # Si el cliente cierra el navegador o pierde la red, atrapamos la excepción
    except WebSocketDisconnect:
        # Si el Host se desconecta, destruimos la sala completa del diccionario global
        if room.code in rooms:
            del rooms[room.code]

# Endpoint WebSocket para los jugadores que se unen vía código
@app.websocket("/join/{room_code}")
async def join_room(
    websocket: WebSocket,
    room_code: str # Parámetro dinámico extraído de la URL
):
    # Aceptamos la conexión entrante del invitado
    await websocket.accept()

    # Validación 1: Verificamos si el código de sala existe en la memoria del servidor
    if room_code not in rooms:
        # Notificamos el error al cliente
        await websocket.send_json({
            "type": "error",
            "message": "Room not found"
        })
        # Cerramos la conexión inmediatamente por seguridad
        await websocket.close()
        return

    # Extraemos la referencia a la sala solicitada
    room = rooms[room_code]

    # Validación 2: Verificamos si la sala ya alcanzó su límite de 4 personas
    if len(room.players) >= room.max_players:
        # Notificamos que la sala está llena
        await websocket.send_json({
            "type": "error",
            "message": "Room full"
        })
        # Rechazamos la conexión
        await websocket.close()
        return

    # Determinamos la posición del nuevo jugador calculando la longitud de la lista
    position = POSITIONS[
        len(room.players)
    ]

    # Instanciamos al nuevo jugador con su socket y la posición calculada
    player = Player(
        websocket,
        position
    )
    # Lo agregamos a la lista oficial de la sala
    room.players.append(player)

    # Notificamos a toda la sala (incluyendo al host) que alguien nuevo entró
    await broadcast_room_status(room)

    # Le confirmamos exclusivamente al nuevo jugador que entró con éxito y su posición
    await websocket.send_json({
        "type": "joined",
        "room": room_code,
        "position": position
    })

    # Bucle de escucha para este cliente invitado
    try:
        import json
        while True:
            # Esperamos comandos de movimiento o estados
            raw = await websocket.receive_text()
            # Deserializamos la cadena
            message = json.loads(raw)
            # Delegamos al procesador central
            await handle_message(
                player,
                room,
                message
            )
            
    # Si este jugador se desconecta de repente...
    except WebSocketDisconnect:
        # Lo buscamos en la lista de la sala
        if player in room.players:
            # Lo eliminamos para liberar el espacio para otra persona
            room.players.remove(player)
        # Notificamos al resto de la sala que este jugador se fue
        await broadcast_room_status(room)