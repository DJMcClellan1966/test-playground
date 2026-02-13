from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Serve frontend static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# File browser endpoint
@app.get("/api/files")
def list_files(path: str = "C:/Users/DJMcC/Desktop"):
    try:
        entries = os.listdir(path)
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            files.append({
                "name": entry,
                "is_dir": os.path.isdir(full_path),
                "path": full_path
            })
        return {"files": files}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

# Download file
@app.get("/api/file")
def get_file(path: str):
    return FileResponse(path)

# Save file
@app.post("/api/file")
async def save_file(request: Request):
    data = await request.json()
    path = data["path"]
    content = data["content"]
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"status": "ok"}

# Agent chat (placeholder)
@app.websocket("/ws/agent")
async def agent_chat(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        # TODO: Integrate app-forge/agent logic here
        await ws.send_text(f"Agent: You said '{data}'")
