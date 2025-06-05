import asyncio
import websockets
import json
from datetime import datetime

async def save_file(file_data, filename=None):
    if not filename:
        filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
    with open(filename, "wb") as file:
        file.write(file_data)
    print(f"Audio saved to {filename}")
    return filename

async def send_request():
    uri = 'wss://uniproxy.alice.yandex.net/uni.ws'
    
    async with websockets.connect(uri) as websocket:
        request = {
            "event": {
                "header": {
                    "messageId": "e9355a7f-6c86-4a49-8c85-2d80532bca90",
                    "name": "Generate",
                    "namespace": "TTS"
                },
                "payload": {
                    "emotion": "neutral",
                    "format": "audio/opus",
                    "lang": "ru-RU",
                    "oauth_token": "",
                    "quality": "UltraHigh",
                    "text": """Аришка какашка""",    # Текст для синтеза речи
                    "voice": "shitova.us"
                }
            }
        }

        print("Sending request...")
        await websocket.send(json.dumps(request))
        print("Request sent")

        audio_data = bytearray()
        stream_active = False
        stream_id = None
        audio_received = False

        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    print(f"Received audio chunk: {len(message)} bytes")
                    audio_data.extend(message)
                    audio_received = True
                    continue
                print(f"Received message: {message}")
                
                try:
                    msg = json.loads(message)
                    if 'directive' in msg:
                        if msg['directive']['header']['name'] == 'Speak':
                            stream_id = msg['directive']['header'].get('streamId')
                            stream_active = True
                            print(f"Audio stream started (ID: {stream_id})")

                    elif 'streamcontrol' in msg:
                        if msg['streamcontrol'].get('streamId') == stream_id:
                            action = msg['streamcontrol'].get('action')
                            if action == 0:
                                print("Stream data sent")
                                break

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    continue

        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        
        finally:
            if audio_data:
                await save_file(audio_data)
            else:
                print("No audio data received")
            await websocket.close()
            print("Connection closed by client")

asyncio.run(send_request())