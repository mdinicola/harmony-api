import json

from quart import Quart
from quart import request

app = Quart(__name__)

@app.route("/health")
async def get_health():
    output = {
        "hub": True,
    }
    return output