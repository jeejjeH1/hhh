# GenLayer Roadmap — motion graphic

16:9 (1920×1080, 60 fps, ~42 s) roadmap video for an X/Twitter post.

- `genlayer-roadmap.mp4` — the finished video (H.264, yuv420p, faststart)
- `roadmap.html` — the animation source. Open it in a browser to watch a live loop.
- `render.mjs` — renders the HTML frame by frame into the MP4 using Playwright + ffmpeg.

## Re-render

```sh
npm i playwright            # or use a global install
node render.mjs genlayer-roadmap.mp4 60
node render.mjs --stills 3,12,40   # quick PNG stills into ./stills
```

Text, dates and timing live at the top of `roadmap.html` (`MILESTONES`, `ARR0`, `STEP`, `HOLD`).
