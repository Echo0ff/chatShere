from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def get(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received: {data}")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
