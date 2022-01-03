import confuse

from functools import wraps
from fastapi import FastAPI, Request
from distutils import util
from helpers import open_client, get_device_from_config
from helpers import validate_command_request, send_commands_to_device

app = FastAPI()
config = confuse.Configuration('App', __name__)
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
            return { 'error': 'API Key not provided or not valid' }, 401
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
async def send_command(request: Request, device_name: str):
    try:
        validate_command_request(request)
    except Exception as e:
        return { 'error': str(e) }, 400

    device = None
    try:
        device = get_device_from_config(config, device_name)
    except Exception as e:
        return { 'error': str(e) }, 404

    commands = request.query_params.get('commands').split(',')
    is_valid = all(command in device['actions'] for command in commands)
    if not is_valid:
        return { 'error': 'At least one of the provided commands is invalid' }, 400

    is_test_run = False
    try:
        is_test_run = request.query_params.get('testRun') and util.strtobool(request.query_params.get('testRun'))
    except ValueError as e:
        return { 'error': str(e) }, 400

    if is_test_run:
        result = {
            'device_id': device['id'],
            'commands': commands,
            'delay': 1
        }
    else:
        async with open_client(HUB_IP) as hub_client: 
            if hub_client is None:
                return { 'error': f'Could not connect to client with IP: {HUB_IP}' }, 500

            result = await send_commands_to_device(hub_client, {
                'device_id': device['id'],
                'commands': commands,
                'delay': 1
            })

    output = { 'result': result }
    return output
