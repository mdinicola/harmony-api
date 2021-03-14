import os
import json
import asyncio
import aioharmony.exceptions

from quart import Quart
from quart import request
from aioharmony.harmonyapi import HarmonyAPI, SendCommandDevice
from aioharmony.responsehandler import Handler
from aioharmony.const import ClientCallbackType, WEBSOCKETS, XMPP

_HUB_IP = os.environ["HARMONY_HUB_IP"]

app = Quart(__name__)

async def get_client(ip_address):
    client = HarmonyAPI(ip_address=ip_address)
    try:
        if await client.connect():
            return client
    except ConnectionRefusedError:
        return None

async def close_client(client):
    if client:
        await asyncio.wait_for(client.close(), timeout=60)

@app.route("/health")
async def get_health():
    hub_client = await get_client(_HUB_IP)
    await close_client(hub_client)

    output = {
        "harmonyHub": hub_client is not None
    }
    return output

if __name__ == "__main__":
    app.run()