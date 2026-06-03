# Importamos la librería asyncio para manejar tareas concurrentes y bucles de tiempo real sin bloquear la ejecución
import asyncio
# Importamos FastAPI y módulos de WebSockets para construir el enrutador y la API del servidor
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
# Importamos HTMLResponse para definir el tipo de contenido devuelto en la ruta principal
from fastapi.responses import HTMLResponse
# Importamos StaticFiles para permitir que el servidor entregue archivos estáticos como game.js
from fastapi.staticfiles import StaticFiles
# Importamos Jinja2Templates para procesar y renderizar el archivo index.html dinámicamente
from fastapi.templating import Jinja2Templates

# Importamos nuestras clases y estructuras de datos personalizadas desde el archivo rooms.py
from rooms import Room, rooms, Player, POSITIONS

# Instanciamos la aplicación central de FastAPI que gestionará todas las peticiones
app = FastAPI()

# Configuramos una ruta de montaje "/static" para que el navegador pueda acceder al directorio "static"
app.mount("/static", StaticFiles(directory="static"), name="static")
# Configuramos el motor de plantillas indicándole que busque los archivos HTML en el directorio "templates"
templates = Jinja2Templates(directory="templates")

# Definimos el endpoint raíz ("/") bajo el método GET para entregar la interfaz de usuario
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Procesamos la petición y devolvemos la plantilla index.html compilada
    return templates.TemplateResponse(request=request, name="index.html")

# Función asíncrona dedicada a informar a todos los clientes sobre quién está en la sala
async def broadcast_room_status(room):
    # Construimos un diccionario (payload) con la metadata actual de la sala y los jugadores
    data = {
        # Definimos el tipo de mensaje para que el frontend sepa cómo enrutarlo
        "type": "room_status",
        # Adjuntamos la cantidad actual de jugadores conectados
        "players": len(room.players),
        # Generamos una lista de diccionarios comprimiendo los datos públicos de cada jugador
        "players_list": [
            {
                # Extraemos el nombre asignado (ej. LEFT)
                "name": player.name,
                # Extraemos la posición cardinal
                "position": player.position,
                # Extraemos el estado booleano de preparación
                "ready": player.ready,
                # Extraemos el color hexadecimal asignado en el backend
                "color": player.color 
            }
            # Iteramos sobre los objetos Player en la lista de la sala
            for player in room.players
        ],
        # Adjuntamos el límite de capacidad de la sala configurado por el host
        "max_players": room.max_players,
        # Adjuntamos el límite de puntos a alcanzar para enviarlo al texto del UI
        "target_score": room.target_score 
    }

    # Creamos una lista temporal para guardar clientes que hayan perdido la conexión TCP
    disconnected = []
    # Iteramos sobre la lista de jugadores activos en la sala
    for player in room.players:
        # Iniciamos un bloque de control de excepciones para prevenir la caída del servidor
        try:
            # Enviamos el payload transformado a formato JSON a través del socket del cliente
            await player.websocket.send_json(data)
        # Si la transmisión falla (el cliente cerró el navegador, perdió red, etc.)
        except Exception:
            # Añadimos al jugador a la lista de desconectados
            disconnected.append(player)

    # Iteramos sobre la lista de jugadores que fallaron
    for player in disconnected:
        # Verificamos por seguridad que sigan registrados en la sala
        if player in room.players:
            # Removemos sus objetos de la memoria para liberar sus espacios
            room.players.remove(player)

# Función asíncrona central que intercepta y procesa los comandos enviados por el cliente
async def handle_message(player, room, message):
    # Si el mensaje recibido indica que el jugador presionó el botón de READY
    if message["type"] == "ready":
        # Modificamos la propiedad booleana del jugador en la memoria del servidor
        player.ready = True
        # Notificamos a todos los clientes para que actualicen sus listas visuales
        await broadcast_room_status(room)
        
        # Evaluamos si la sala ya está completamente llena según su límite (2 o 4)
        if len(room.players) == room.max_players:
            # Verificamos mediante 'all' si la propiedad 'ready' es True para absolutamente todos
            all_ready = all(p.ready for p in room.players)
            
            # Si todos están listos y el motor físico aún no ha sido arrancado
            if all_ready and not room.game_state.started:
                # Ordenamos al motor físico habilitar el cálculo inyectando el número de jugadores
                room.game_state.start_game(len(room.players))
                
                # Preparamos el payload de notificación de arranque de partida
                start_data = {"type": "game_start"}
                # Iteramos sobre todos los jugadores conectados
                for p in room.players:
                    try:
                        # Les despachamos la orden para que cambien sus pantallas a la de juego
                        await p.websocket.send_json(start_data)
                    except:
                        # Ignoramos fallos silenciosamente en esta etapa para no trabar el ciclo
                        pass
                        
    # Si el mensaje es un comando de movimiento proveniente del teclado del cliente
    elif message["type"] == "input":
        # Extraemos la referencia al motor de físicas específico de esta sala
        game = room.game_state
        # Inyectamos el comando delegándolo al método de control, pasando posición, tecla y estado
        game.set_input(player.position, message["key"], message["pressed"])

# Función asíncrona que empaqueta todo el estado matemático y lo transmite en tiempo real
async def broadcast_game_state(room):
    # Obtenemos la referencia directa al motor de juego de la sala
    game = room.game_state
    
    # Construimos el diccionario de estado general del fotograma
    data = {
        # Identificador del paquete para el router del frontend
        "type": "game_state",
        # Posición horizontal actual de la pelota
        "ball_x": game.ball_x,
        # Posición vertical actual de la pelota
        "ball_y": game.ball_y,
        # Matriz completa con las posiciones unidimensionales de las paletas
        "paddles": game.paddles,
        # Indicador de cuántos jugadores rigen las reglas de este fotograma
        "active_players": game.active_players,
        # Matriz con los puntajes actualizados de todos los jugadores
        "scores": game.scores,             
        # El límite de puntos necesario para renderizar el subtítulo dinámico
        "target_score": game.target_score, 
        # Bandera booleana que dicta si la partida debe detenerse
        "game_over": game.game_over,       
        # Cadena de texto con la posición del ganador si lo hubiera
        "winner": game.winner              
    }

    # Iteramos la lista de jugadores activos
    for player in room.players:
        try:
            # Enviamos el gran diccionario convertido en cadena JSON por el socket
            await player.websocket.send_json(data)
        except:
            # Protegemos el bucle de envío si un cliente se cae en medio del fotograma
            pass

# Tarea asíncrona que mantiene vivo el bucle de renderizado y físicas del servidor
async def game_loop(room):
    # Iniciamos un ciclo infinito que durará mientras la sala exista
    while True:
        # Obtenemos la instancia matemática
        game = room.game_state
        # Ejecutamos las matemáticas de colisión y movimiento
        game.update()
        # Transmitimos el estado resultante a las interfaces de los clientes
        await broadcast_game_state(room)
        # Suspendemos la ejecución de esta corrutina 1/60 de segundo para forzar los 60 FPS
        await asyncio.sleep(1/60)

# Endpoint WebSocket para el creador de la sala, inyectando parámetros de configuración por URL
@app.websocket("/host")
async def host_room(websocket: WebSocket, max_players: int = 4, target_score: int = 10):
    # Ejecutamos el protocolo de enlace manual para aceptar la conexión entrante
    await websocket.accept()
    
    # Creamos un nuevo objeto de sala pasándole las configuraciones extraídas de la URL
    room = Room(max_players=max_players, target_score=target_score)
    # Almacenamos la sala en el registro global del servidor
    rooms[room.code] = room

    # Desatamos la tarea del bucle físico en segundo plano para no bloquear este endpoint
    asyncio.create_task(game_loop(room))

    # Creamos al jugador Host y le asignamos la primera posición del arreglo
    player = Player(websocket, POSITIONS[0])
    # Registramos al jugador en la lista oficial de la sala
    room.players.append(player)

    # Ordenamos una actualización general de la vista del lobby
    await broadcast_room_status(room)

    # Enviamos un mensaje privado al host confirmando la creación y su color/posición
    await websocket.send_json({
        "type": "room_created",
        "code": room.code,
        "position": player.position 
    })

    # Bucle infinito para recibir los paquetes de comandos del Host
    try:
        # Importamos json localmente para parsear los datos en crudo
        import json
        while True:
            # Detenemos la ejecución esperando a recibir una cadena de texto
            raw = await websocket.receive_text()
            # Deserializamos la cadena a un diccionario de Python
            message = json.loads(raw)
            # Pasamos la orden al procesador general
            await handle_message(player, room, message)
    # Capturamos la desconexión del cliente creador
    except WebSocketDisconnect:
        # Verificamos si la sala aún existe en la memoria
        if room.code in rooms:
            # Eliminamos la sala completa destruyendo la partida si el host sale
            del rooms[room.code]

# Endpoint WebSocket dinámico para que los invitados se unan mediante un código en la ruta
@app.websocket("/join/{room_code}")
async def join_room(websocket: WebSocket, room_code: str):
    # Aceptamos el apretón de manos inicial del socket
    await websocket.accept()

    # Validamos si el código proporcionado no existe en el registro global
    if room_code not in rooms:
        # Informamos del error estructural al cliente
        await websocket.send_json({"type": "error", "message": "Room not found"})
        # Cerramos abruptamente la conexión
        await websocket.close()
        # Salimos de la función
        return

    # Extraemos la instancia de la sala solicitada
    room = rooms[room_code]

    # Validamos si la sala ya igualó o superó su capacidad máxima permitida
    if len(room.players) >= room.max_players:
        # Despachamos el error de límite de cupo
        await websocket.send_json({"type": "error", "message": "Room full"})
        # Cerramos la conexión sobrante
        await websocket.close()
        # Salimos de la función
        return

    # Determinamos la posición del invitado usando el tamaño de la lista como índice
    position = POSITIONS[len(room.players)]
    # Creamos el objeto del jugador invitado
    player = Player(websocket, position)
    # Lo adjuntamos a la sala
    room.players.append(player)

    # Informamos a todos en el lobby del nuevo ingreso
    await broadcast_room_status(room)

    # Le confirmamos exclusivamente al nuevo jugador sus credenciales de sesión
    await websocket.send_json({
        "type": "joined",
        "room": room_code,
        "position": position 
    })

    # Iniciamos el bucle de recepción de datos para este invitado
    try:
        import json
        while True:
            # Recibimos el paquete crudo
            raw = await websocket.receive_text()
            # Deserializamos
            message = json.loads(raw)
            # Inyectamos en el procesador general
            await handle_message(player, room, message)
    # Capturamos si este jugador específico abandona la sesión
    except WebSocketDisconnect:
        # Si el jugador sigue registrado en la memoria de la sala
        if player in room.players:
            # Lo eliminamos limpiamente
            room.players.remove(player)
        # Notificamos al resto de la sala que el espacio se liberó
        await broadcast_room_status(room)