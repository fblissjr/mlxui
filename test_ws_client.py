import asyncio
import websockets
import json

async def test_generation_stream():
    uri = "ws://127.0.0.1:8000/api/generate/ws" # Ensure port matches your backend
    
    generation_request = {
        "prompt": "Hello, world! Tell me a short story.",
        "max_tokens": 50,
        "temperature": 0.7,
        # Add other GenerationRequest fields as needed
    }

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            await websocket.send(json.dumps(generation_request))
            print(f"Sent request: {generation_request['prompt'][:30]}...")

            while True:
                message_str = await websocket.recv()
                chunk = json.loads(message_str)
                
                if chunk.get("error"):
                    print(f"\nError from server: {chunk['error']}")
                    break
                
                print(chunk.get("text", ""), end="", flush=True)
                
                if chunk.get("is_finished"):
                    print(f"\nStream finished. Reason: {chunk.get('finish_reason')}")
                    break
    except websockets.exceptions.ConnectionClosedOK:
        print("\nConnection closed normally by server.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    # Ensure your FastAPI backend is running before executing this script.
    # And ensure a model is loaded in the backend.
    print("Attempting to connect to WebSocket for generation...")
    print("Make sure a model is loaded in the backend (e.g., via curl POST to /api/models/load).")
    asyncio.run(test_generation_stream())