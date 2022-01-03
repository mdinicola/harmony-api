import asyncio
import aioharmony.exceptions

from contextlib import asynccontextmanager
from aioharmony.harmonyapi import HarmonyAPI, SendCommandDevice
from aioharmony.responsehandler import Handler
from aioharmony.const import ClientCallbackType, WEBSOCKETS, XMPP

async def get_client(ip_address):
    client = HarmonyAPI(ip_address=ip_address)
    try:
        if await client.connect():
            return client
        else:
            return None
    except Exception:
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
    if args.get('device_id').isdigit():
        if client.get_device_name(int(args.get('device_id'))):
            device_id = args.get('device_id')
    
    if device_id is None:
        device_id = client.get_device_id(str(args.get('device_id')).strip())
    
    if device_id is None:
        return False

    commands_list = args.get('commands')
    delay = args.get('delay')
    snd_cmmnd_list = []

    for command in commands_list:
        snd_cmmnd = SendCommandDevice(
            device=device_id,
            command=command,
            delay=args.get('delay'))
        snd_cmmnd_list.append(snd_cmmnd)

    result_list = await client.send_commands(snd_cmmnd_list)

    if result_list:
        return False
    else:
        return True

def get_device_from_config(config, name):
    device_list = list(filter(lambda x: x['name'] == name, config['devices'].get()))
    device_list_length = len(device_list)
    if device_list_length > 1:
        raise KeyError(f'Muliple devices found with name: {name}')
    if device_list_length == 0:
        raise KeyError(f'No devices found with name: {name}')
    return device_list[0]    
    
def validate_command_request(request):
    if request.query_params.get('device') is None:
        raise Exception('No device proviced')
    if request.query_params.get('commands') is None:
        raise Exception('No commands provided')
    return True