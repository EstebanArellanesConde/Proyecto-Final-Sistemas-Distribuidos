import asyncio
import websockets

ROOM = input("Código de sala: ")


async def join():

    uri = f"ws://127.0.0.1:8000/join/{ROOM}"

    async with websockets.connect(uri) as ws:

        while True:

            msg = await ws.recv()

            print(msg)


asyncio.run(join())