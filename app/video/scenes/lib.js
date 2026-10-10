// Shared drawing kit for the VANI explainer scenes (IndiaMART template, 1920x1080 canvas).
const c = document.getElementById('c'), x = c.getContext('2d');
const NAVY = '#002060', RED = '#C00000', TEAL = '#2EA896', ORANGE = '#E08A00', PURPLE = '#5B3E96', GREY = '#9aa3b2', INK = '#262626', CLAUDE = '#D97757';
const TPL = new Image(); TPL.src = '../assets/template_bg.jpg';
window.READY = new Promise(r => { TPL.onload = r; TPL.onerror = r; });

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const ease = p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const back = p => { p = clamp(p); const s = 1.7; return 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2); };
const seg = (lt, a, b) => ease((lt - a) / (b - a));
const lerp = (a, b, p) => a + (b - a) * p;
function mix(c1, c2, p) { const h = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16)); const A = h(c1), B = h(c2);
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], clamp(p))).toString(16).padStart(2, '0')).join(''); }
function alpha(a, fn) { if (a <= 0) return; x.save(); x.globalAlpha *= clamp(a); fn(); x.restore(); }
function scaled(cx, cy, s, fn) { if (s <= 0) return; x.save(); x.translate(cx, cy); x.scale(s, s); x.translate(-cx, -cy); fn(); x.restore(); }

function bg() { x.fillStyle = '#fff'; x.fillRect(0, 0, 1920, 1080); if (TPL.naturalWidth) x.drawImage(TPL, 0, 0, 1920, 1080); }
// every label ≥ 48 px, with a white halo so lines never cross text
function txt(s, px, py, size, color = INK, align = 'center', bold = false) { size = Math.max(size, 48); x.font = `${bold ? 'bold ' : ''}${size}px Arial`; x.textAlign = align; x.textBaseline = 'middle';
  x.save(); x.strokeStyle = '#fff'; x.lineWidth = 12; x.lineJoin = 'round'; x.strokeText(s, px, py); x.restore(); x.fillStyle = color; x.fillText(s, px, py); }
function emoji(s, px, py, size) { x.font = `${size}px "Segoe UI Emoji"`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = INK; x.fillText(s, px, py); }
function rr(px, py, w, h, r, fill, stroke, lw = 4, dash) { x.save(); if (dash) x.setLineDash(dash); x.beginPath(); x.roundRect(px, py, w, h, r); if (fill) { x.fillStyle = fill; x.fill(); } if (stroke) { x.strokeStyle = stroke; x.lineWidth = lw; x.stroke(); } x.restore(); }
function ln(a, b, c2, d, color, w = 5, dash, p = 1) { if (p <= 0) return; x.save(); x.strokeStyle = color; x.lineWidth = w; x.lineCap = 'round'; if (dash) x.setLineDash(dash);
  x.beginPath(); x.moveTo(a, b); x.lineTo(lerp(a, c2, p), lerp(b, d, p)); x.stroke(); x.restore(); }
function arrow(a, b, c2, d, color, w = 6, p = 1) { if (p <= 0) return; const ex = lerp(a, c2, p), ey = lerp(b, d, p), an = Math.atan2(d - b, c2 - a);
  ln(a, b, c2, d, color, w, null, p); x.save(); x.fillStyle = color; x.beginPath(); x.moveTo(ex, ey); x.lineTo(ex - 26 * Math.cos(an - .45), ey - 26 * Math.sin(an - .45)); x.lineTo(ex - 26 * Math.cos(an + .45), ey - 26 * Math.sin(an + .45)); x.closePath(); x.fill(); x.restore(); }
function title(s, a = 1) { alpha(a, () => { x.fillStyle = NAVY; x.font = 'bold 66px Arial'; x.textAlign = 'left'; x.textBaseline = 'middle'; x.fillText(s, 80, 95); x.fillStyle = RED; x.fillRect(80, 138, 160, 7); }); }
function chip(px, py, w, label, color = ORANGE, icon = '', s = 1) { scaled(px + w / 2, py, s, () => { rr(px, py - 50, w, 100, 50, '#fff', color, 5);
  if (icon) emoji(icon, px + 60, py, 52); txt(label, px + (icon ? 105 : w / 2), py, 48, INK, icon ? 'left' : 'center', true); }); }
// Claude mark: a simple orange starburst (illustrative, not the official logo file)
function spark(cx, cy, r, rot = 0) { x.save(); x.translate(cx, cy); x.rotate(rot); x.fillStyle = CLAUDE;
  for (let i = 0; i < 12; i++) { x.rotate(Math.PI / 6); x.beginPath(); x.ellipse(0, -r * .55, r * .11, r * .45, 0, 0, 6.3); x.fill(); } x.restore(); }

// timeline: beats draw from local progress p (0..1) and local time lt (s, at the designed base length)
function timeline(BEATS) {
  function layout() { let acc = 0; BEATS.forEach(b => { b.dur = b.dur || b.base; b.start = acc; acc += b.dur; });
    window.BEATS = BEATS.map(({ n, dur, start, base, title: t, vo, sound, move }) => ({ n, dur, start, base, title: t, vo, sound, move })); window.DURATION = acc; }
  layout();
  window.setDurs = ds => { ds.forEach((d, i) => { if (BEATS[i]) BEATS[i].dur = d; }); layout(); };
  window.renderFrame = T => { const b = BEATS.find(b => T < b.start + b.dur) || BEATS[BEATS.length - 1]; const k = b.base / b.dur, lt = (T - b.start) * k; bg(); b.draw(clamp(lt / b.base), lt, T * k); };
}
