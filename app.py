import confuse
import distutils

from functools import wraps
from quart import Quart, request
from distutils import util
from helpers import open_client, get_device_from_config
from helpers import validate_command_request, send_commands_to_device

app = Quart(__name__)
config = confuse.Configuration('App', __name__)
config.set_file('config/config.yml')

API_KEY = config['api_key'].get()
HUB_IP = config['hub_ip'].get()
COMMAND_DELAY = config['command_delay'].get(int)

def require_apikey(view_function):
    @wraps(view_function)
    async def decorated_function(*args, **kwargs):
        if request.args.get('apikey') and request.args.get('apikey') == API_KEY:
            return await view_function(*args, **kwargs)
        else:
            return { 'error': 'API Key not provided or not valid' }, 401
    return decorated_function

@app.route('/health')
@require_apikey
async def get_health():
    async with open_client(HUB_IP) as hub_client:
        output = {
            'healthy': hub_client is not None
        }
        return output

@app.route('/sendCommandsToDevice', methods=['POST'])
@require_apikey
async def send_command():
    try:
        validate_command_request(request)
    except Exception as e:
        return { 'error': str(e) }, 400

    device = None
    try:
        device = get_device_from_config(config, request.args.get('device'))
    except Exception as e:
        return { 'error': str(e) }, 404
    
    commands = request.args.get('commands').split(',')
    is_valid = all(command in device['actions'] for command in commands)
    if not is_valid:
        return { 'error': 'At least one of the provided commands is not valid' }, 400

    try:
        is_test_run = request.args.get('testRun') and distutils.util.strtobool(request.args.get('testRun'))
    except ValueError as e:
        return { 'error': str(e) }, 400

    if request.args.get('testRun') and distutils.util.strtobool(request.args.get('testRun')):
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

if __name__ == '__main__':
    app.run()
