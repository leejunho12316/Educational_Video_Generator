import sys
import json
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil

# 프로젝트 루트를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
from Video_Generator_Agent import run as run_agent

# pip install fastapi uvicorn python-multipart
# uvicorn backend.main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent.parent / "ppt_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

VIDEO_OUTPUTS = Path(__file__).parent.parent / "video_outputs"
VIDEO_OUTPUTS.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "frontend"), name="static")
app.mount("/videos", StaticFiles(directory=VIDEO_OUTPUTS), name="videos")


def write_status(ppt_name: str, data: dict):
    out_dir = VIDEO_OUTPUTS / ppt_name
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "status.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


DEFAULT_TONE  = "친절하고 명료한 강의 톤"
DEFAULT_STYLE = "예시와 핵심 요점 중심"


def run_job(pptx_path: str, ppt_name: str, prompt: dict):
    try:
        write_status(ppt_name, {"status": "running", "file": Path(pptx_path).name})
        result = run_agent(pptx_path=pptx_path, prompt=prompt)
        write_status(ppt_name, {
            "status": "done",
            "file": Path(pptx_path).name,
            "final_video": result.get("final_video", ""),
        })
    except Exception as e:
        write_status(ppt_name, {
            "status": "error",
            "file": Path(pptx_path).name,
            "error": str(e),
        })


@app.post("/upload")
async def upload_ppt(
    file:  UploadFile = File(...),
    voice: str = Form("alloy"),
    tone:  str = Form(""),
    style: str = Form(""),
):
    if not file.filename.lower().endswith((".pptx", ".ppt")):
        raise HTTPException(status_code=400, detail="pptx 또는 ppt 파일만 업로드 가능합니다.")

    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    prompt = {
        "voice": voice,
        "tone":  tone  or DEFAULT_TONE,
        "style": style or DEFAULT_STYLE,
    }

    ppt_name = Path(file.filename).stem
    write_status(ppt_name, {"status": "pending", "file": file.filename})

    thread = threading.Thread(target=run_job, args=(str(dest), ppt_name, prompt), daemon=True)
    thread.start()

    return {"filename": file.filename, "ppt_name": ppt_name}


@app.get("/output-status/{ppt_name}")
async def output_status(ppt_name: str):
    status_file = VIDEO_OUTPUTS / ppt_name / "status.json"
    if not status_file.exists():
        return {"status": "not_started"}
    with open(status_file, encoding="utf-8") as f:
        return json.load(f)


@app.get("/files")
async def list_files():
    files = sorted(
        [p for p in UPLOAD_DIR.iterdir() if p.suffix.lower() in (".pptx", ".ppt")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return {"files": [f.name for f in files]}