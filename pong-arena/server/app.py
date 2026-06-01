import asyncio
from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from rooms import Room
from rooms import rooms
from rooms import Player
from rooms import POSITIONS

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

async def broadcast_room_status(room):

    data = {
        "type": "room_status",
        "players": len(room.players),
        "positions": [
            player.position
            for player in room.players
        ],
        "max_players": room.max_players
    }

    disconnected = []

    for player in room.players:

        try:

            await player.websocket.send_json(data)

        except Exception:

            disconnected.append(player)

    for player in disconnected:

        if player in room.players:

            room.players.remove(player)

async def broadcast_game_state(room):

    game = room.game_state

    data = {
        "type": "game_state",
        "ball_x": game.ball_x,
        "ball_y": game.ball_y
    }

    for player in room.players:

        try:

            await player.websocket.send_json(data)

        except:
            pass

async def game_loop(room):

    while True:

        game = room.game_state

        game.update()

        await broadcast_game_state(room)

        await asyncio.sleep(1/30)

@app.websocket("/host")
async def host_room(websocket: WebSocket):

    await websocket.accept()

    room = Room()

    rooms[room.code] = room

    asyncio.create_task(
        game_loop(room)
    )

    player = Player(
        websocket,
        POSITIONS[0]
    )

    room.players.append(player)

    await broadcast_room_status(room)

    await websocket.send_json({
        "type": "room_created",
        "code": room.code
    })

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        if room.code in rooms:

            del rooms[room.code]


@app.websocket("/join/{room_code}")
async def join_room(
    websocket: WebSocket,
    room_code: str
):

    await websocket.accept()

    if room_code not in rooms:

        await websocket.send_json({
            "type": "error",
            "message": "Room not found"
        })

        await websocket.close()

        return

    room = rooms[room_code]

    if len(room.players) >= room.max_players:

        await websocket.send_json({
            "type": "error",
            "message": "Room full"
        })

        await websocket.close()

        return

    position = POSITIONS[
        len(room.players)
    ]

    player = Player(
        websocket,
        position
    )

    room.players.append(player)

    await broadcast_room_status(room)

    await websocket.send_json({
        "type": "joined",
        "room": room_code,
        "position": position
    })

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        if player in room.players:

            room.players.remove(player)

        await broadcast_room_status(room)