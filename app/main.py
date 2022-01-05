import confuse

from functools import wraps
from fastapi import FastAPI, Request, HTTPException

from models.command import Command
from helpers import open_client, get_device_from_config
from helpers import send_commands_to_device

app = FastAPI()
config = confuse.Configuration('HarmonyApi')
config.set_file('config/config.yml')

API_KEY = config['api_key'].get()
HUB_IP = config['hub_ip'].get()
COMMAND_DELAY = config['command_delay'].get(int)

def require_apikey(view_function):
    @wraps(view_function)
    async def decorated_function(request, *args, **kwargs):
        if request.query_params.get('apikey') and request.query_params.get('apikey') == API_KEY:
            return await view_function(request, *args, **kwargs)
        else:
            raise HTTPException(status_code = 400, detail = "API key was either not provided or is invalid")
    return decorated_function

@app.get('/health')
@require_apikey
async def get_health(request: Request):
    async with open_client(HUB_IP) as hub_client:
        output = {
            'healthy': hub_client is not None
        }
        return output

@app.post('/devices/{device_name}')
@require_apikey
async def send_command_to_device(request: Request, device_name: str, command: Command, testRun: bool = False):
    device = None
    try:
        device = get_device_from_config(config, device_name)
    except Exception:
        raise HTTPException(status_code = 404, detail = f'Device with name {device_name} could not be found')

    commands = command.commands
    is_valid = len(commands) != 0
    is_valid = is_valid and all(command in device['commands'] for command in commands)
    if not is_valid:
        raise HTTPException(status_code = 400, detail = 'At least one of the provided commands is invalid')

    if testRun:
        result = {
            'device_id': device['id'],
            'commands': commands,
            'delay': 1
        }
    else:
        async with open_client(HUB_IP) as hub_client: 
            if hub_client is None:
                raise HTTPException(status_code = 500, detail = f'Could not connect to client with IP: {HUB_IP}')

            result = await send_commands_to_device(hub_client, {
                'device_id': device['id'],
                'commands': commands,
                'delay': 1
            })

    output = { 'result': result }
    return output
