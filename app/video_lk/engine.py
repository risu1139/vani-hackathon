"""Small 2D animation engine: sprites with timed entrances and exits, rendered with PIL and piped to ffmpeg."""
import math
import os
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
SS = 2  # supersampling for smooth edges
HERE = os.path.dirname(os.path.abspath(__file__))

NAVY, RED, TEAL, ORANGE, PURPLE = (0, 32, 96), (192, 0, 0), (46, 168, 150), (224, 138, 0), (91, 62, 150)
INK, GREY, LIGHT, WHITE, GREEN = (38, 38, 38), (120, 120, 120), (238, 242, 248), (255, 255, 255), (27, 107, 94)
SOFT = (200, 200, 200)

_fonts = {}


def font(size, bold=True):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype("C:/Windows/Fonts/" + ("arialbd.ttf" if bold else "arial.ttf"), size)
    return _fonts[k]


def wrap(text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if fnt.getlength(t) <= maxw or not line:
                line = t
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def _down(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def _draw_text(d, cx, top, lines, fnt, color, align="center", left=0):
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * 1.12)
    for i, ln in enumerate(lines):
        if align == "center":
            d.text((cx, top + i * lh), ln, font=fnt, fill=color, anchor="ma")
        else:
            d.text((left, top + i * lh), ln, font=fnt, fill=color, anchor="la")
    return lh * len(lines)


def text(s, size=44, color=INK, bold=True, maxw=1600, align="center"):
    fnt = font(size * SS, bold)
    lines = wrap(s, fnt, maxw * SS)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * 1.12)
    w = int(max(fnt.getlength(x) for x in lines)) + 8 * SS
    h = lh * len(lines) + 6 * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _draw_text(d, w // 2, 0, lines, fnt, color, align, left=4 * SS)
    return _down(img)


def box(w, h, fill, title=None, sub=None, tsize=40, ssize=28, tcolor=WHITE, scolor=None, radius=26, outline=None, width=4,
        align="center", pad=28):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=radius * SS, fill=fill, outline=outline,
                        width=(width * SS if outline else 0))
    scolor = scolor or tcolor
    blocks = []
    if title:
        f1 = font(tsize * SS, True)
        blocks.append((wrap(title, f1, (w - 2 * pad) * SS), f1, tcolor))
    if sub:
        f2 = font(ssize * SS, False)
        blocks.append((wrap(sub, f2, (w - 2 * pad) * SS), f2, scolor))
    hts = []
    for lines, f, _ in blocks:
        a, de = f.getmetrics()
        hts.append(int((a + de) * 1.12) * len(lines))
    gap = 10 * SS
    total = sum(hts) + gap * (len(hts) - 1 if hts else 0)
    y = (h * SS - total) // 2
    for (lines, f, c), ht in zip(blocks, hts):
        _draw_text(d, w * SS // 2, y, lines, f, c, align, left=pad * SS)
        y += ht + gap
    return _down(img)


def circle(dia, fill, label=None, size=40, color=WHITE, outline=None, width=5):
    img = Image.new("RGBA", (dia * SS, dia * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, dia * SS - 1, dia * SS - 1], fill=fill, outline=outline, width=(width * SS if outline else 0))
    if label:
        f = font(size * SS, True)
        lines = wrap(label, f, int(dia * 0.78) * SS)
        a, de = f.getmetrics()
        lh = int((a + de) * 1.12)
        _draw_text(d, dia * SS // 2, (dia * SS - lh * len(lines)) // 2, lines, f, color)
    return _down(img)


def arrow(length, color=GREY, thick=16, head=34, direction="r"):
    L, T, Hd = length * SS, thick * SS, head * SS
    img = Image.new("RGBA", (L, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    mid = Hd // 2
    d.rectangle([0, mid - T // 2, L - Hd, mid + T // 2], fill=color)
    d.polygon([(L - Hd - 2, 0), (L, mid), (L - Hd - 2, Hd)], fill=color)
    img = _down(img)
    return {"r": img, "l": img.transpose(Image.FLIP_LEFT_RIGHT), "d": img.rotate(-90, expand=True),
            "u": img.rotate(90, expand=True)}[direction]


def line(x0, y0, x1, y1, color=RED, width=14):
    """A straight stroke as a sprite; returns (sprite, x, y)."""
    pad = width
    xa, ya = min(x0, x1) - pad, min(y0, y1) - pad
    w, h = abs(x1 - x0) + 2 * pad, abs(y1 - y0) + 2 * pad
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([((x0 - xa) * SS, (y0 - ya) * SS), ((x1 - xa) * SS, (y1 - ya) * SS)], fill=color, width=width * SS)
    return _down(img), xa, ya


def ease(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


class El:
    """A sprite on screen. anim: pop | fade | up | left | wipe | stamp."""

    def __init__(self, img, x, y, t0, t1=None, anim="pop", dur=0.5, center=False):
        self.img, self.t0, self.t1, self.anim, self.dur = img, t0, t1, anim, dur
        if center:
            x, y = x - img.width // 2, y - img.height // 2
        self.x, self.y = int(x), int(y)
        self._a = img.getchannel("A")

    def state(self, t):
        if t < self.t0:
            return None
        pin = (t - self.t0) / self.dur
        pout = 0.0 if self.t1 is None else (t - self.t1) / 0.35
        if pout >= 1:
            return None
        return min(1.0, pin), max(0.0, pout)

    def draw(self, frame, t):
        st = self.state(t)
        if st is None:
            return
        pin, pout = st
        e = ease(pin)
        alpha = e * (1 - ease(pout))
        img, x, y = self.img, self.x, self.y
        if self.anim in ("pop", "stamp") and e < 1:
            s = (0.6 if self.anim == "pop" else 1.8) + ((0.4 if self.anim == "pop" else -0.8) * e)
            nw, nh = max(1, int(img.width * s)), max(1, int(img.height * s))
            img = img.resize((nw, nh), Image.BILINEAR)
            x, y = self.x + (self.img.width - nw) // 2, self.y + (self.img.height - nh) // 2
        elif self.anim == "up":
            y = self.y + int(40 * (1 - e))
        elif self.anim == "left":
            x = self.x - int(60 * (1 - e))
        elif self.anim == "wipe" and e < 1:
            cw = max(1, int(img.width * e))
            img = img.crop((0, 0, cw, img.height))
        if alpha < 0.999:
            img = img.copy()
            a = img.getchannel("A").point(lambda v: int(v * alpha))
            img.putalpha(a)
        # clip to frame
        if x >= W or y >= H or x + img.width <= 0 or y + img.height <= 0:
            return
        cx0, cy0 = max(0, -x), max(0, -y)
        if cx0 or cy0 or x + img.width > W or y + img.height > H:
            img = img.crop((cx0, cy0, min(img.width, W - x), min(img.height, H - y)))
            x, y = x + cx0, y + cy0
        frame.alpha_composite(img, dest=(x, y))

    def busy(self, t):
        st = self.state(t)
        if st is None:
            return self.t0 <= t  # just exited: one more redraw is harmless
        return st[0] < 1 or st[1] > 0


def render(elements, total, out_path, bg_path, fps=FPS, preview_every=None):
    bg = Image.open(bg_path).convert("RGBA").resize((W, H))
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(math.ceil(total * fps))
    last_key, last_bytes = None, None
    for i in range(n):
        t = i / fps
        live = [e for e in elements if e.t0 <= t and (e.t1 is None or t < e.t1 + 0.35)]
        key = tuple(id(e) for e in live)
        if key == last_key and not any(e.busy(t) for e in live):
            p.stdin.write(last_bytes)
            continue
        frame = bg.copy()
        for e in live:
            e.draw(frame, t)
        last_bytes = frame.convert("RGB").tobytes()
        last_key = key
        p.stdin.write(last_bytes)
        if preview_every and i % preview_every == 0:
            frame.convert("RGB").save(os.path.join(os.path.dirname(out_path), f"prev_{i // fps:04d}.jpg"), quality=80)
    p.stdin.close()
    p.wait()
    return n


def still(elements, t, bg_path):
    frame = Image.open(bg_path).convert("RGBA").resize((W, H))
    for e in elements:
        e.draw(frame, t)
    return frame.convert("RGB")
