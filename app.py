import confuse

from helpers import open_client, get_device_from_config
from helpers import validate_command_request, send_commands_to_device
from quart import Quart, request

app = Quart(__name__)
config = confuse.Configuration('App', __name__)
config.set_file('config/config.yml')

HUB_IP = config['hub_ip'].get()
COMMAND_DELAY = config['command_delay'].get(int)

@app.route('/health')
async def get_health():
    async with open_client(HUB_IP) as hub_client:
        output = {
            'healthy': hub_client is not None
        }
        return output

@app.route('/sendCommandsToDevice', methods=['POST'])
async def send_command():
    try:
        validate_command_request(request)
    except Exception as e:
        return { 'error': e }, 400

    device = None
    try:
        device = get_device_from_config(config, request.args.get('device'))
    except Exception as e:
        return { 'error': e }, 400
    
    commands = request.args.get('commands').split(',')
    is_valid = all(command in device['actions'] for command in commands)
    if not is_valid:
        return { 'error': 'At least one of the provided commands is not valid' }, 400

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
