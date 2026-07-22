# Lecture Slide Extractor — Setup Guide (VS Code)

This gets you a **working local prototype** first: paste a video link, get back
a folder of slide images + one PDF.

## Run it

```bash
python extract_slides.py "https://www.youtube.com/watch?v=SOME_LECTURE_ID"
```

This will:
- Download the video into a temp folder (auto-deleted after)
- Sample a frame every 1 second
- Save each unique slide to `./output/slides/`
- Compile them into `./output/lecture_slides.pdf`

Optional flags:
```bash
python extract_slides.py "URL" --interval 2.0 --threshold 8 --out ./my_output
```
- `--interval` — seconds between sampled frames (higher = faster, may miss quick slides)
- `--threshold` — how different a frame must be to count as a "new slide" (lower = more sensitive, may over-detect)