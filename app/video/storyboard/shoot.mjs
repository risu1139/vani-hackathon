// Screenshot a storyboard page to PNG. Usage: node storyboard/shoot.mjs storyboard/scenes_1_2.html
import { chromium } from 'playwright';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const src = path.resolve(process.argv[2]);
const out = src.replace(/\.html$/, '.png');
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
await p.goto(pathToFileURL(src).href);
await p.waitForFunction(() => window.DONE === true);
await p.screenshot({ path: out, fullPage: true });
await b.close();
console.log(out);
