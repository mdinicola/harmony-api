# harmony-api
Simple API to send commands to Harmony Hub

## Health Endpoint

GET https://url/health?apikey=xxx
Response should be 

    {"healthy":true}

## Send Commands to device

POST to https://url/devices/devicename?apikey=xxx
    
    {
        "commands": [
            "PowerToggle"
        ]
    }
