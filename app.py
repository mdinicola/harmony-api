import os
import json
import asyncio
import aioharmony.exceptions
import confuse

from contextlib import asynccontextmanager
from quart import Quart
from quart import request
from aioharmony.harmonyapi import HarmonyAPI, SendCommandDevice
from aioharmony.responsehandler import Handler
from aioharmony.const import ClientCallbackType, WEBSOCKETS, XMPP

app = Quart(__name__)
config = confuse.Configuration("App", __name__)
config.set_file("config/config.yml")

HUB_IP = config["hub_ip"].get()

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

@asynccontextmanager
async def open_client(client_ip):
    client = await get_client(client_ip)
    yield client
    await close_client(client)

async def send_commands_to_device(client, args):
    device_id = None
    if args.get("device_id").isdigit():
        if client.get_device_name(int(args.get("device_id"))):
            device_id = args.get("device_id")
    
    if device_id is None:
        device_id = client.get_device_id(str(args.get("device_id")).strip())
    
    if device_id is None:
        return False

    commands_list = args.get("commands")
    delay = args.get("delay")
    snd_cmmnd_list = []

    for command in commands_list:
        snd_cmmnd = SendCommandDevice(
            device=device_id,
            command=command,
            delay=args.get("delay"))
        snd_cmmnd_list.append(snd_cmmnd)

    result_list = await client.send_commands(snd_cmmnd_list)

    if result_list:
        return False
    else:
        return True

@app.route("/health")
async def get_health():
    async with open_client(HUB_IP) as hub_client:
        output = {
            "healthy": hub_client is not None
        }
        return output

@app.route("/commands")
async def send_command():
    async with open_client(HUB_IP) as hub_client:
        commands = request.args.get("commands")
        if commands is None:
            return { "error": "No commands provided" }, 400
        
        commands_list = commands.split(",")
        result = await send_commands_to_device(hub_client, {
            "device_id": request.args.get("deviceid"),
            "commands": commands_list,
            "delay": 1
        })

        output = { "result": result }
        return output

if __name__ == "__main__":
    app.run()