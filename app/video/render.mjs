// Render a scene page frame by frame to MP4, plus a contact sheet for review.
// Usage: node render.mjs <scene.html> [fps=30] [--beats] [--only=9,11] [--durs=beat_lengths.json]   (--beats: one clip per beat, for review before merging)
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const scene = path.resolve(process.argv[2]);
const fps = Number(process.argv[3] || 30);
const perBeat = process.argv.includes('--beats');
const name = path.basename(scene, '.html');
const out = path.join(HERE, 'build', name);
mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(scene).href);
await page.evaluate(() => window.READY);
const dursArg = process.argv.find(a => a.startsWith('--durs='));
if (dursArg) await page.evaluate(d => window.setDurs(d), JSON.parse((await import('node:fs')).readFileSync(dursArg.slice(7), 'utf8')));
const dur = await page.evaluate(() => window.DURATION);
const only = (process.argv.find(a => a.startsWith('--only=')) || '').slice(7).split(',').filter(Boolean).map(Number);
let beats = perBeat ? await page.evaluate(() => window.BEATS) : [{ n: 'all', start: 0, dur }];
if (only.length) beats = beats.filter(b => only.includes(b.n));

const ff = (...a) => execFileSync('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...a]);
for (const b of beats) {
  const tag = b.n === 'all' ? name : `${name}_beat${String(b.n).padStart(2, '0')}`;
  const frames = path.join(out, 'frames', tag);
  rmSync(frames, { recursive: true, force: true }); mkdirSync(frames, { recursive: true });
  const n = Math.round(b.dur * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.renderFrame(t), b.start + i / fps);
    await page.screenshot({ path: path.join(frames, `f${String(i).padStart(5, '0')}.png`) });
  }
  const mp4 = path.join(out, `${tag}.mp4`);
  ff('-framerate', String(fps), '-i', path.join(frames, 'f%05d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', mp4);
  // contact sheet: 4 frames per second of the clip, 6 across
  ff('-i', mp4, '-vf', `fps=2,scale=480:-1,tile=6x${Math.ceil(b.dur * 2 / 6)}`, '-frames:v', '1', path.join(out, `${tag}_sheet.png`));
  console.log('done', mp4);
}
await browser.close();
