"""
Lecture Slide Extractor
------------------------
Given a video link (YouTube, Vimeo, direct file, etc.), this script:
  1. Downloads the video using yt-dlp
  2. Samples frames at a fixed interval using OpenCV
  3. Detects slide changes by comparing perceptual hashes of frames
  4. Saves one image per unique slide
  5. Compiles the slides into a single PDF

Usage:
    python extract_slides.py "https://www.youtube.com/watch?v=XXXXXXX"

Optional flags:
    --out ./slides           output folder (default: ./output)
    --interval 1.0            seconds between sampled frames (default: 1.0)
    --threshold 6              hash distance threshold for "new slide" (default: 6, lower = stricter)
"""

import argparse
import os
import shutil
import subprocess
import sys

import cv2
import imagehash
from PIL import Image


def download_video(url: str, workdir: str) -> str:
    """Download video with yt-dlp, return path to the downloaded file."""
    out_template = os.path.join(workdir, "lecture.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", out_template,
        url,
    ]
    print(f"[1/4] Downloading video from: {url}")
    subprocess.run(cmd, check=True)

    for f in os.listdir(workdir):
        if f.startswith("lecture."):
            return os.path.join(workdir, f)
    raise FileNotFoundError("Download finished but no output file was found.")


def extract_unique_frames(video_path: str, out_dir: str, interval: float, threshold: int):
    """Sample frames at `interval` seconds and keep only ones that differ enough
    from the previously kept frame (i.e. an actual slide change)."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_step = max(int(fps * interval), 1)

    print(f"[2/4] Video FPS: {fps:.1f} — sampling every {interval}s ({frame_step} frames)")

    frame_idx = 0
    saved_count = 0
    last_hash = None

    os.makedirs(out_dir, exist_ok=True)

    while True:
        ret = cap.grab()
        if not ret:
            break

        if frame_idx % frame_step == 0:
            ret, frame = cap.retrieve()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            current_hash = imagehash.phash(pil_img)

            if last_hash is None or (current_hash - last_hash) > threshold:
                saved_count += 1
                out_path = os.path.join(out_dir, f"slide_{saved_count:03d}.png")
                pil_img.save(out_path)
                last_hash = current_hash
                print(f"    -> saved {out_path}")

        frame_idx += 1

    cap.release()
    print(f"[3/4] Done. Extracted {saved_count} unique slide(s).")
    return saved_count


def compile_pdf(slides_dir: str, pdf_path: str):
    """Combine all slide images into a single PDF, in order."""
    import img2pdf

    images = sorted(
        os.path.join(slides_dir, f)
        for f in os.listdir(slides_dir)
        if f.lower().endswith(".png")
    )
    if not images:
        print("No slides found to compile into a PDF.")
        return

    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(images))
    print(f"[4/4] PDF saved to: {pdf_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract slides from a lecture video link.")
    parser.add_argument("url", help="Lecture video URL")
    parser.add_argument("--out", default="./output", help="Output folder for slides + PDF")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between sampled frames")
    parser.add_argument("--threshold", type=int, default=6, help="Hash distance threshold for a new slide")
    args = parser.parse_args()

    workdir = os.path.join(args.out, "_tmp_video")
    slides_dir = os.path.join(args.out, "slides")
    pdf_path = os.path.join(args.out, "lecture_slides.pdf")

    os.makedirs(workdir, exist_ok=True)

    try:
        video_path = download_video(args.url, workdir)
        extract_unique_frames(video_path, slides_dir, args.interval, args.threshold)
        compile_pdf(slides_dir, pdf_path)
    finally:
        # Clean up the downloaded video to save disk space (comment out to keep it)
        shutil.rmtree(workdir, ignore_errors=True)

    print("\nAll done! Check the output folder:", args.out)


if __name__ == "__main__":
    main()