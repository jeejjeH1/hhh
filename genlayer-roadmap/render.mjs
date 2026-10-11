// Renders roadmap.html frame-by-frame and pipes the frames into ffmpeg.
// Usage: node render.mjs [out.mp4] [fps]          -> full video
//        node render.mjs --stills t1,t2,...        -> PNG stills into ./stills
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(here, 'roadmap.html')).href + '?render');
await page.evaluate(() => document.fonts.ready);
await page.addStyleTag({ content: 'canvas{width:1920px!important;height:1080px!important;margin:0!important}' });
const canvas = page.locator('canvas');

if (args[0] === '--stills') {
  mkdirSync(path.join(here, 'stills'), { recursive: true });
  for (const t of args[1].split(',').map(Number)) {
    await page.evaluate(t => window.render(t), t);
    await canvas.screenshot({ path: path.join(here, 'stills', `t${t.toFixed(2)}.png`) });
  }
} else {
  const out = args[0] || path.join(here, 'genlayer-roadmap.mp4');
  const fps = Number(args[1] || 60);
  const duration = await page.evaluate(() => window.DURATION);
  const frames = Math.round(duration * fps);
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-maxrate', '20M', '-bufsize', '40M',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.render(t), f / fps);
    const buf = await canvas.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 120 === 0) console.error(`frame ${f}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
