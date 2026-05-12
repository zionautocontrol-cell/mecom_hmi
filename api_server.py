import json
import base64
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sqlite3
import uvicorn
from config import (
    DB_PATH,
    REALTIME_JSON,
    CONTROL_COMMAND_JSON,
    DIAGRAM_HTML,
    BACKGROUND_IMAGE,
)

app = FastAPI(title="MECOM API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_background_base64() -> str:
    if not BACKGROUND_IMAGE.exists():
        return ""
    try:
        with open(BACKGROUND_IMAGE, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""


@app.get("/realtime")
def get_realtime():
    try:
        return json.loads(REALTIME_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "disconnected", "bits": [False] * 38, "words": [0.0] * 11, "accum_heat": 0.0}


@app.get("/control")
def get_control():
    try:
        return json.loads(CONTROL_COMMAND_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"command": "none", "status": "idle", "message": ""}


@app.get("/history")
def get_history(limit: int = 100):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM history_logs ORDER BY timestamp DESC LIMIT {limit}")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}


@app.get("/hmi", response_class=HTMLResponse)
def get_hmi():
    try:
        data = json.loads(REALTIME_JSON.read_text(encoding="utf-8"))
    except Exception:
        data = {"bits": [False] * 38, "words": [0.0] * 11, "accum_heat": 0.0}

    bits = data.get("bits", [False] * 38)
    words = data.get("words", [0.0] * 11)

    if not DIAGRAM_HTML.exists():
        return HTMLResponse("<h2>diagram.html not found</h2>", status_code=404)

    html = DIAGRAM_HTML.read_text(encoding="utf-8")

    bg = load_background_base64()
    if bg:
        html = html.replace("{{BACKGROUND_IMAGE}}", bg)

    for i in range(38):
        val = bits[i] if i < len(bits) else False
        if i < 30:
            cls = "running" if val else "paused"
        else:
            cls = "on" if val else "off"
        html = html.replace(f"{{{{B{i}}}}}", cls)

    for i in range(11):
        val = words[i] if i < len(words) else 0.0
        html = html.replace(f"{{{{W{i}}}}}", f"{val:.1f}")

    return HTMLResponse(html)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
