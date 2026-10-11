# GenLayer Roadmap — motion graphic

16:9 (1920×1080, 60 fps, 42 s) roadmap video with a soundtrack, made for an X/Twitter post.

- `genlayer-roadmap.mp4` — the finished video (H.264 + AAC, faststart)
- `roadmap.html` — the animation source. Open it in a browser to watch a live (silent) loop.
- `render.mjs` — renders the HTML frame by frame (4 parallel parts) into `genlayer-roadmap-silent.mp4`.
- `soundtrack.py` — synthesises the music and sound effects, timed to the animation, into `soundtrack.wav`.
- `mux.sh` — combines the two into `genlayer-roadmap.mp4`.

## Re-render

```sh
npm i playwright            # or use a global install
pip install numpy scipy
node render.mjs genlayer-roadmap-silent.mp4 60 4
python3 soundtrack.py
./mux.sh
node render.mjs --stills 3,12,40   # quick PNG stills into ./stills
```

Text, dates and timing live at the top of `roadmap.html` (`MILESTONES`, `ARR0`, `STEP`, `HOLD`).
If you change timing, update the event times at the top of `soundtrack.py` to match.
