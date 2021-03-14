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
COMMAND_DELAY = config["command_delay"].get(int)

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

def get_device_from_config(config, name):
    device_list = list(filter(lambda x: x["name"] == name, config["devices"].get()))
    device_list_length = len(device_list)
    if device_list_length > 1:
        raise KeyError(f"Muliple devices found with name: {name}")
    if device_list_length == 0:
        raise KeyError(f"No devices found with name: {name}")
    return device_list[0]    
    
def validate_command_request(request):
    if request.args.get("device") is None:
        raise Exception("No device proviced")
    if request.args.get("commands") is None:
        raise Exception("No commands provided")
    return True

@app.route("/health")
async def get_health():
    async with open_client(HUB_IP) as hub_client:
        output = {
            "healthy": hub_client is not None
        }
        return output

@app.route("/sendCommandsToDevice", methods=['POST'])
async def send_command():
    async with open_client(HUB_IP) as hub_client:
        try:
            validate_command_request(request)
        except Exception as e:
            return { "error": e }, 400

        device = None
        try:
            device = get_device_from_config(config, request.args.get("device"))
        except Exception as e:
            return { "error": e }, 400
        
        commands = request.args.get("commands").split(",")
        is_valid = all(command in device["actions"] for command in commands)
        if not is_valid:
            return { "error": "At least one of the provided commands is not valid" }, 400
        
        result = await send_commands_to_device(hub_client, {
            "device_id": request.args.get("deviceid"),
            "commands": commands,
            "delay": 1
        })

        output = { "result": result }
        return output

if __name__ == "__main__":
    app.run()
