# Startale App — Two new USDC vaults (motion graphic)

16:9 (1920×1080, 60 fps, 26 s) video with a soundtrack for the X/Twitter post announcing the
Gauntlet USDC Prime and Flowmark fGenesis vaults on Startale App, styled after the "New Ways to Earn" key visual.

- `startale-usdc-vaults.mp4` — the finished video (H.264 + AAC, faststart)
- `vaults.html` — the animation source (canvas 2D + three.js for the coin, safe and voxel block).
  Serve the folder (`npx serve .`) and open `vaults.html` for a live, silent loop; add `?t=12` to start at 12 s.
- `render.mjs` — renders the HTML frame by frame (4 parallel parts) into `startale-usdc-vaults-silent.mp4`.
- `soundtrack.py` — synthesises the music and sound effects, timed to the animation, into `soundtrack.wav`.
- `mux.sh` — combines the two into `startale-usdc-vaults.mp4`.
- `assets/logos/*.svg` — partner logos vectorised from the key visual by `tools/trace_logos.py`
  (the Startale mark, Gauntlet G and Asseto square are redrawn on their pixel grid).
- `assets/fonts/` — Poppins (OFL), `vendor/` — three.js r170 (MIT).

## Storyboard

| time | scene |
| --- | --- |
| 0–2.7 s | Startale mark assembles from 8 pieces, wordmark reveals, lockup docks top-left |
| 2.7–7.2 s | "Two new USDC vaults on Startale App" — a 3D safe rises, two USDC coins drop into its slot |
| 7.2–11.7 s | Iris through the coin → Vault 01: Gauntlet USDC Prime, curated by @gauntlet_xyz, BTC/ETH collateral orbit |
| 11.7–16.2 s | Branded wipe → Vault 02: Flowmark fGenesis, curated by @Flowmark_xyz, PGNGI+ block tokenised by @AssetoFinance |
| 16.2–19.7 s | Both vaults flow into the Morpho butterfly — "Powered by Morpho" |
| 19.7–26 s | End card mirroring the key visual: New Ways to Earn, CTA "Deposit now and start earning ↓", partner logos, disclaimer |

## Re-render

```sh
npm i playwright            # or link a global install into node_modules
pip install numpy scipy
node render.mjs startale-usdc-vaults-silent.mp4 60 4
python3 soundtrack.py
./mux.sh
node render.mjs --stills 3,9,24   # quick PNG stills into ./stills
```

Timing lives in `T` at the top of `vaults.html`; if you change it, update the event times at the top of `soundtrack.py`.
