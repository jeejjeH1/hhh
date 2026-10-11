// Renders roadmap.html frame-by-frame and pipes the frames into ffmpeg.
// Usage: node render.mjs [out.mp4] [fps] [workers]  -> full video (silent), rendered in parallel parts
//        node render.mjs --stills t1,t2,...          -> PNG stills into ./stills
// Add the soundtrack afterwards with: python3 soundtrack.py && ./mux.sh
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const browser = await chromium.launch();

async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.join(here, 'roadmap.html')).href + '?render');
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: 'canvas{width:1920px!important;height:1080px!important;margin:0!important}' });
  return page;
}
const run = (cmd, a) => new Promise((res, rej) => {
  const p = spawn(cmd, a, { stdio: ['ignore', 'ignore', 'inherit'] });
  p.on('close', c => c === 0 ? res() : rej(new Error(`${cmd} exited ${c}`)));
});

async function renderPart(f0, f1, fps, out) {
  const page = await openPage();
  const canvas = page.locator('canvas');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-maxrate', '20M', '-bufsize', '40M',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.render(t), f / fps);
    const buf = await canvas.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 120 === 0) console.error(`[${path.basename(out)}] frame ${f}/${f1}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await page.close();
}

if (args[0] === '--stills') {
  const page = await openPage();
  const canvas = page.locator('canvas');
  mkdirSync(path.join(here, 'stills'), { recursive: true });
  for (const t of args[1].split(',').map(Number)) {
    await page.evaluate(t => window.render(t), t);
    await canvas.screenshot({ path: path.join(here, 'stills', `t${t.toFixed(2)}.png`) });
  }
} else {
  const out = args[0] || path.join(here, 'genlayer-roadmap-silent.mp4');
  const fps = Number(args[1] || 60);
  const workers = Number(args[2] || 4);
  const probe = await openPage();
  const frames = Math.round(await probe.evaluate(() => window.DURATION) * fps);
  await probe.close();
  const tmp = path.join(here, '.parts');
  mkdirSync(tmp, { recursive: true });
  const per = Math.ceil(frames / workers);
  const parts = [];
  for (let k = 0; k < workers; k++) {
    const f0 = k * per, f1 = Math.min(frames, f0 + per);
    if (f0 < f1) parts.push({ f0, f1, file: path.join(tmp, `part${k}.mp4`) });
  }
  await Promise.all(parts.map(p => renderPart(p.f0, p.f1, fps, p.file)));
  const list = path.join(tmp, 'list.txt');
  writeFileSync(list, parts.map(p => `file '${p.file}'`).join('\n'));
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', out]);
  rmSync(tmp, { recursive: true });
}
await browser.close();
