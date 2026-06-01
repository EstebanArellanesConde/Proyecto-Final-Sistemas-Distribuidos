import asyncio
import websockets
import json


async def create_room():

    uri = "ws://127.0.0.1:8000/host"

    async with websockets.connect(uri) as ws:

        while True:

            msg = await ws.recv()

            print(msg)


asyncio.run(create_room())