"""
FastAPI server that wraps the slide extractor.
Run with: uvicorn api:app --reload
Then open: http://127.0.0.1:8000/docs to test it in your browser.
"""

import os
import uuid
import threading

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from extract_slides import download_video, extract_unique_frames, compile_pdf

app = FastAPI()

# Simple in-memory job store (fine for local testing; a real app would use a database)
JOBS = {}

BASE_OUTPUT_DIR = "./api_output"
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

# Serve the output folder so files can be downloaded via URL
app.mount("/files", StaticFiles(directory=BASE_OUTPUT_DIR), name="files")


class ExtractRequest(BaseModel):
    url: str
    interval: float = 1.0
    threshold: int = 12


def run_job(job_id: str, url: str, interval: float, threshold: int):
    job_dir = os.path.join(BASE_OUTPUT_DIR, job_id)
    workdir = os.path.join(job_dir, "_tmp_video")
    slides_dir = os.path.join(job_dir, "slides")
    pdf_path = os.path.join(job_dir, "lecture_slides.pdf")
    os.makedirs(workdir, exist_ok=True)

    try:
        JOBS[job_id]["status"] = "downloading"
        video_path = download_video(url, workdir)

        JOBS[job_id]["status"] = "extracting"
        count = extract_unique_frames(video_path, slides_dir, interval, threshold)

        JOBS[job_id]["status"] = "compiling"
        compile_pdf(slides_dir, pdf_path)

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["slide_count"] = count
        JOBS[job_id]["pdf_url"] = f"/files/{job_id}/lecture_slides.pdf"
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)


@app.post("/extract")
def extract(req: ExtractRequest):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "queued"}
    thread = threading.Thread(target=run_job, args=(job_id, req.url, req.interval, req.threshold))
    thread.start()
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def status(job_id: str):
    return JOBS.get(job_id, {"status": "not_found"})