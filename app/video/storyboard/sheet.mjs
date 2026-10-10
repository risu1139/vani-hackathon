// Storyboard sheet from a scene file: one still per beat (its last frame), with time, title, voice line, sound and move.
// Usage: node storyboard/sheet.mjs scenes/scene3.html "Scene 3 · From data to persona"
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const scene = path.resolve(process.argv[2]);
const heading = process.argv[3] || path.basename(scene, '.html');
const name = path.basename(scene, '.html');
const dir = path.join(HERE, '..', 'build', name, 'stills'); mkdirSync(dir, { recursive: true });

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
await p.goto(pathToFileURL(scene).href); await p.evaluate(() => window.READY);
const beats = await p.evaluate(() => window.BEATS);
for (const bt of beats) {
  await p.evaluate(t => window.renderFrame(t), bt.start + bt.dur - 0.05);
  await p.locator('canvas').screenshot({ path: path.join(dir, `beat${String(bt.n).padStart(2, '0')}.png`) });
}
const total = beats.reduce((s, x) => s + x.dur, 0).toFixed(1);
const cards = beats.map(bt => `<div class="panel"><img src="${pathToFileURL(path.join(dir, `beat${String(bt.n).padStart(2, '0')}.png`)).href}">
  <div class="t"><span>${bt.n}</span>${bt.start.toFixed(1)}s · ${bt.title}</div><div class="vo">“${bt.vo}”</div><div class="s">sound: ${bt.sound}<br>→ ${bt.move}</div></div>`).join('');
const html = `<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#f3f5f9;font-family:Arial;color:#262626}
.page{width:1920px;padding:40px 56px;box-sizing:border-box}h1{margin:0;font-size:46px;color:#002060}.bar{width:120px;height:6px;background:#C00000;margin:12px 0}
.meta{font-size:22px;color:#595959;margin-bottom:24px}.row{display:grid;grid-template-columns:repeat(2,1fr);gap:28px}
.panel{background:#fff;border:1px solid #d9dee8;border-radius:10px;padding:10px}img{width:100%;border-radius:6px;border:1px solid #eef2f8;display:block}
.t{font-size:26px;font-weight:bold;margin:10px 0 4px}.t span{color:#C00000;margin-right:8px}.vo{font-size:22px;font-style:italic;margin-bottom:6px}.s{font-size:20px;color:#595959}</style>
<div class="page"><h1>VANI explainer: storyboard, ${heading}</h1><div class="bar"></div><div class="meta">~${total} s (before voice timing) · ${beats.length} beats · seller values are illustrative. Thumbs up or down by panel number.</div><div class="row">${cards}</div></div>`;
const out = path.join(HERE, `${name}.html`); writeFileSync(out, html);
await p.setViewportSize({ width: 1920, height: 1080 }); await p.goto(pathToFileURL(out).href);
await p.screenshot({ path: out.replace(/\.html$/, '.png'), fullPage: true });
await b.close(); console.log(out.replace(/\.html$/, '.png'));
