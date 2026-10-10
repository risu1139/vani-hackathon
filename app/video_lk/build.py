"""Builds the VANI Persona Design pitch video (silent; timed to the voice lines of outputs/plans/video-script-3min.md).

Usage: python app/video_lk/build.py [--only 3] [--preview]
Beat length = audio length when app/video_lk/audio/<beat>.wav exists, else words / 2.15 + 0.35 s.
Output: app/video_lk/build/vani_persona_pitch.mp4 (git-ignored).
"""
import argparse
import os
import re
import wave

from engine import (GREEN, GREY, INK, LIGHT, NAVY, ORANGE, PURPLE, RED, TEAL, WHITE, El, arrow, box, circle, line, render,
                    text)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPT = os.path.join(ROOT, "outputs", "plans", "video-script-3min.md")
BG = os.path.join(HERE, "bg.png")
OUT = os.path.join(HERE, "build")
LEAD = 0.4       # silence at the start of each scene, while the title arrives
TAIL = 0.3       # pause after the last beat of a scene


def beats():
    rows = {}
    for ln in open(SCRIPT, encoding="utf-8"):
        m = re.match(r"\|\s*(\d\.\d)\s*\|(.*?)\|(.*?)\|\s*$", ln)
        if m:
            rows[m.group(1)] = {"screen": m.group(2).strip(), "voice": m.group(3).strip()}
    return rows


def beat_len(bid, voice):
    wav = os.path.join(HERE, "audio", f"{bid}.wav")
    if os.path.exists(wav):
        with wave.open(wav) as w:
            return w.getnframes() / w.getframerate() + 0.35
    return len(voice.split()) / 2.15 + 0.35


class Scene:
    def __init__(self, t0, title, ids, rows):
        self.t0, self.title, self.els = t0, title, []
        self.B = {}
        t = t0 + LEAD
        for i in ids:
            self.B[i] = t
            t += beat_len(i, rows[i]["voice"])
        self.end = t + TAIL
        if title:
            self.add(text(title, 64, NAVY), 124, 98, t0 + 0.05, anim="left", dur=0.6)

    def add(self, img, x, y, t, anim="pop", dur=0.5, center=False, until=None):
        e = El(img, x, y, t, until if until is not None else self.end - 0.35, anim, dur, center)
        self.els.append(e)
        return e

    def at(self, bid, off=0.0):
        return self.B[bid] + off


# ---------------------------------------------------------------- scenes
def intro(t0, rows):
    s = Scene(t0, None, [], rows)
    s.end = t0 + 3.2
    s.add(text("Persona Design", 120, NAVY), 960, 430, t0 + 0.1, center=True, until=s.end - 0.35)
    s.add(text("A voice persona for every seller, adapting live during the call", 44, GREY, bold=False), 960, 560,
          t0 + 0.6, anim="up", center=True, until=s.end - 0.35)
    s.add(box(760, 80, RED, "Problem 4  |  Voice AI Hackathon 2.0", tsize=34), 960, 690, t0 + 1.0, center=True,
          until=s.end - 0.35)
    return s


def scene1(t0, rows):
    s = Scene(t0, "The Gap", ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"], rows)
    xs = [180, 330, 480, 630, 780]
    for i, x in enumerate(xs):
        s.add(circle(110, NAVY, "Seller", 24), x - 55, 600, s.at("1.1", 0.1 + i * 0.12))
        for k, col in enumerate((TEAL, ORANGE, RED)):
            s.add(circle(22, col), x - 40 + k * 28, 725, s.at("1.1", 0.8 + i * 0.12 + k * 0.08), anim="fade")
    s.add(text("IndiaMART knows each seller", 34, GREY), 480, 790, s.at("1.1", 1.2), center=True, anim="up")
    s.add(box(520, 150, GREEN, "Objective", "a meeting with an IndiaMART executive", tsize=42, ssize=30), 1280, 280, s.at("1.2", 0.1))
    s.add(box(340, 100, GREY, "SAME SCRIPT", tsize=40), 310, 290, s.at("1.3", 0.0))
    for i, x in enumerate(xs):
        s.add(arrow(160, (175, 175, 175), direction="d"), x - 17, 410, s.at("1.3", 0.4 + i * 0.12), anim="wipe")
    s.add(circle(110, RED, "Rush", 28), 425, 600, s.at("1.4", 0.0), anim="stamp")
    s.add(text("26%", 140, NAVY), 1300, 560, s.at("1.5", 0.0), center=True)
    s.add(arrow(140, GREY), 1440, 545, s.at("1.5", 0.5), anim="wipe")
    s.add(text("14%", 140, RED), 1700, 560, s.at("1.5", 0.9), center=True, anim="stamp")
    s.add(text("meetings when the seller is rushed", 32, GREY, bold=False), 1500, 670, s.at("1.5", 1.2), center=True, anim="up")
    s.add(box(1680, 100, PURPLE, "Persona: the bridge between each seller and the meeting", tsize=42), 120, 850, s.at("1.6", 0.0), anim="left")
    return s


def scene2(t0, rows):
    s = Scene(t0, "Rich Context, No Personal Data", ["2.1", "2.2", "2.3", "2.4", "2.5"], rows)
    cx, cy = 700, 610
    chips = [("Business", 700, 360, NAVY), ("Catalogue", 293, 485, RED), ("Buy leads", 1107, 485, TEAL),
             ("Competitors", 293, 735, PURPLE), ("Past calls", 1107, 735, ORANGE)]
    for i, (lab, x, y, col) in enumerate(chips):
        img, lx, ly = line(cx, cy, x, y, (200, 200, 200), 6)
        s.add(img, lx, ly, s.at("2.2", 0.0 + i * 0.45), anim="fade")
        s.add(box(300, 90, col, lab, tsize=36), x, y, s.at("2.2", 0.05 + i * 0.45), center=True)
    s.add(circle(250, NAVY, "SELLER", 44), cx, cy, s.at("2.1", 0.1), center=True)
    s.add(text("62", 170, RED), 1575, 330, s.at("2.1", 0.6), center=True, anim="stamp")
    s.add(text("data points per seller", 38, GREY, bold=False), 1575, 440, s.at("2.1", 1.0), center=True, anim="up")
    s.add(box(450, 120, TEAL, "Each one:", "a reason to meet", tsize=36, ssize=34), 1350, 520, s.at("2.3", 0.0))
    s.add(box(450, 110, NAVY, "Personal data removed", tsize=36), 1350, 680, s.at("2.4", 0.0))
    s.add(box(450, 120, LIGHT, "Names → tokens", "Phone, GST, PAN stay inside IndiaMART", tsize=34, ssize=27, tcolor=NAVY,
              scolor=INK, outline=NAVY), 1350, 810, s.at("2.5", 0.0))
    s.add(box(300, 64, TEAL, "{SELLER_NAME}", tsize=30), cx, cy + 70, s.at("2.5", 0.4), center=True, anim="stamp")
    return s


def scene3(t0, rows):
    s = Scene(t0, "Traits and States", ["3.1", "3.2", "3.3", "3.4"], rows)
    import random
    rnd = random.Random(7)
    for k in range(24):
        s.add(circle(26, (175, 175, 175)), 130 + rnd.randint(0, 230), 300 + rnd.randint(0, 230), s.at("3.1", 0.05 * k), anim="fade",
              dur=0.3)
    s.add(text("Raw data", 34, GREY), 255, 560, s.at("3.1", 0.6), center=True, anim="fade")
    s.add(arrow(120, GREY), 410, 405, s.at("3.1", 1.4), anim="wipe")
    s.add(box(360, 150, NAVY, "Facts", "computed by code", tsize=48, ssize=30), 560, 340, s.at("3.1", 2.0))
    s.add(box(800, 140, NAVY, "TRAITS: who the seller is", "business size, division, language", tsize=40, ssize=30), 1000, 300,
          s.at("3.2", 0.0))
    s.add(box(800, 140, ORANGE, "STATES: what is happening now", "buy-lead use, enquiry flow, recent call mood", tsize=40, ssize=30),
          1000, 470, s.at("3.3", 0.0))
    for k in range(6):                       # signals fade with age: half every 30 days
        hgt = int(150 * 0.5 ** (k / 2))
        s.add(box(70, hgt, ORANGE, radius=8), 1080 + k * 95, 800 - hgt, s.at("3.3", 1.2 + k * 0.15), anim="up")
    s.add(text("older signals count less", 30, ORANGE), 1080, 812, s.at("3.3", 2.2), anim="fade")
    s.add(box(860, 110, PURPLE, "Same data in → same facts out", tsize=42), 120, 690, s.at("3.4", 0.0), anim="left")
    return s


def scene4(t0, rows):
    s = Scene(t0, "A Persona for Each Seller", ["4.1", "4.2", "4.3", "4.4", "4.5"], rows)
    P = [("P0", "Default", GREY), ("P1", "Numbers-first", NAVY), ("P2", "Warm local", RED), ("P3", "Patient", TEAL),
         ("P4", "Brief", ORANGE), ("P5", "Problem-solver", PURPLE), ("P6", "Senior", GREEN)]
    for i, (pid, name, col) in enumerate(P):
        x = 300 + i * 220
        s.add(circle(110, col, pid, 38), x, 310, s.at("4.1", 0.3 + i * 0.15), center=True)
        s.add(text(name, 24, INK), x, 392, s.at("4.1", 0.5 + i * 0.15), center=True, anim="fade")
    s.add(box(620, 56, RED, "Every choice cites the seller's data", tsize=30), 960, 462, s.at("4.2", 0.3), center=True, anim="stamp")
    ex = [("Small-town trader", "P2 Warm local", RED, 740), ("Busy distributor", "P4 Brief, one line", ORANGE, 1180),
          ("Large manufacturer", "P6 Senior advisor", GREEN, 1620)]
    for i, (who, pers, col, px) in enumerate(ex):
        x = 120 + i * 570
        s.add(box(520, 120, col, who, pers, tsize=34, ssize=30), x, 515, s.at("4.3", 0.1 + i * 1.6))
        s.add(circle(136, (0, 0, 0, 0), outline=col, width=6), px, 310, s.at("4.3", 0.3 + i * 1.6), center=True, anim="stamp")
    hooks = [("Live order", NAVY), ("Weak catalogue", RED), ("Category demand", TEAL), ("Unused credits", PURPLE),
             ("Lead quality", ORANGE), ("Enquiry drop", GREY), ("Similar sellers", GREEN), ("Fix a complaint", (138, 28, 28))]
    for i, (h, col) in enumerate(hooks):
        r, c = divmod(i, 4)
        s.add(box(400, 66, col, h, tsize=30), 120 + c * 425, 670 + r * 80, s.at("4.4", 0.2 + i * 0.15))
    s.add(box(1680, 70, WHITE, "Changes delivery. Never facts or prices.", tsize=36, tcolor=NAVY, outline=NAVY),
          120, 845, s.at("4.5", 0.0), anim="up")
    return s


def scene5(t0, rows):
    s = Scene(t0, "The Live Call", ["5.1", "5.2", "5.3", "5.4"], rows)
    s.add(box(1680, 100, TEAL, "START: voice, pace, language, opening line", tsize=42), 120, 260, s.at("5.1", 0.1), anim="left")
    R = [("5.2", 0.8, "“Abhi busy hoon”", "One line + a callback", ORANGE),
         ("5.3", 0.0, "“Samajh nahi aaya”", "One simple idea", PURPLE),
         ("5.3", 1.8, "Marathi → Hindi", "VANI follows", NAVY)]
    for k, (bid, off, said, does, col) in enumerate(R):
        y = 400 + k * 130
        s.add(box(720, 100, LIGHT, said, tsize=40, tcolor=INK, outline=(180, 180, 180)), 120, y, s.at(bid, off), anim="left")
        s.add(arrow(120, col), 870, y + 33, s.at(bid, off + 0.5), anim="wipe")
        s.add(box(780, 100, col, does, tsize=40), 1020, y, s.at(bid, off + 0.8))
    s.add(box(1680, 100, GREEN, "Meeting booked with the seller's own executive", tsize=42), 120, 800, s.at("5.4", 0.1), anim="up")
    return s


def scene6(t0, rows):
    s = Scene(t0, "The Agent Decides", ["6.1", "6.2", "6.3", "6.4"], rows)
    s.add(box(460, 200, LIGHT, "Rule table", "same type, same answer", tsize=44, ssize=30, tcolor=GREY, scolor=GREY,
              outline=(180, 180, 180)), 120, 280, s.at("6.1", 0.1))
    for (a, b, c, d) in ((140, 300, 560, 460), (560, 300, 140, 460)):
        img, x, y = line(a, b, c, d, RED, 12)
        s.add(img, x, y, s.at("6.1", 1.4), anim="stamp")
    s.add(box(380, 170, TEAL, "Scoreboards", "top 2 personas for similar sellers", tsize=40, ssize=27), 650, 295, s.at("6.2", 0.0))
    s.add(arrow(100, GREY), 1045, 363, s.at("6.2", 0.8), anim="wipe")
    s.add(circle(230, RED, "Agent reads this seller", 32), 1160, 265, s.at("6.2", 1.6))
    for i, lab in enumerate(["Persona", "Hook", "12 fields"]):
        s.add(box(220, 66, NAVY, lab, tsize=30), 1430, 285 + i * 80, s.at("6.2", 2.4 + i * 0.25))
    st = [("1  Seller evidence", RED), ("2  Earlier calls", TEAL), ("3  Default", GREY)]
    for i, (h, col) in enumerate(st):
        x = 120 + i * 440
        s.add(box(390, 110, col, h, tsize=36), x, 600, s.at("6.3", 0.6 + i * 1.3))
        if i < 2:
            s.add(arrow(40, GREY), x + 395, 637, s.at("6.3", 1.3 + i * 1.3), anim="wipe")
    s.add(box(360, 110, NAVY, "Validator", tsize=38), 1440, 600, s.at("6.4", 0.0))
    s.add(box(760, 100, RED, "No evidence? REFUSED. NO CALL.", tsize=36), 1040, 760, s.at("6.4", 1.6), anim="stamp")
    return s


def scene7(t0, rows):
    s = Scene(t0, "Mood Engine", ["7.1", "7.2"], rows)
    s.add(box(340, 490, LIGHT, "Seller turn", "what was just said", tsize=40, ssize=28, tcolor=NAVY, scolor=GREY,
              outline=(180, 180, 180)), 120, 280, s.at("7.1", 0.0))
    s.add(arrow(150, TEAL), 480, 348, s.at("7.1", 0.5), anim="wipe")
    s.add(box(640, 170, TEAL, "In the call: keyword tool", "under 1 ms, Hindi, Marathi, Telugu", tsize=40, ssize=30), 650, 280, s.at("7.1", 0.8))
    s.add(arrow(90, TEAL), 1300, 348, s.at("7.1", 1.6), anim="wipe")
    s.add(box(410, 170, RED, "VANI changes now", tsize=40), 1400, 280, s.at("7.1", 1.9))
    s.add(arrow(150, NAVY), 480, 668, s.at("7.2", 0.0), anim="wipe")
    s.add(box(640, 170, NAVY, "Between calls: Jev", "a decision model labels real turns", tsize=40, ssize=30), 650, 600, s.at("7.2", 0.3))
    s.add(arrow(90, NAVY), 1300, 668, s.at("7.2", 1.1), anim="wipe")
    s.add(box(410, 170, PURPLE, "Labels", "where the keyword tool was wrong", tsize=40, ssize=28), 1400, 600, s.at("7.2", 1.4))
    s.add(arrow(120, PURPLE, direction="u"), 1316, 470, s.at("7.2", 2.4), anim="fade")
    s.add(text("teaches the keyword tool", 30, PURPLE), 1370, 505, s.at("7.2", 2.6), anim="fade")
    return s


def scene8(t0, rows):
    s = Scene(t0, "The Self-Learning Loop", ["8.1", "8.2", "8.3"], rows)
    N = {"call": ("1  CALL", "persona + hook logged", TEAL, 749, 240), "review": ("2  REVIEW", "Claude + our rules", NAVY, 1296, 400),
         "outcome": ("3  OUTCOME", "meeting or not", GREEN, 1166, 660), "credit": ("4  CREDIT", "persona, hook, each field", RED, 331, 660),
         "brief": ("5  BRIEF", "next agent reads what worked", PURPLE, 202, 400)}

    def node(k, t):
        h, sub, col, x, y = N[k]
        s.add(box(420, 140, col, h, sub, tsize=40, ssize=27), x, y, t)
    node("call", s.at("8.1", 0.0))
    s.add(arrow(110, GREY), 1180, 285, s.at("8.1", 0.8), anim="wipe")
    node("review", s.at("8.1", 1.1))
    s.add(arrow(110, GREY, direction="d"), 1490, 548, s.at("8.1", 2.6), anim="wipe")
    node("outcome", s.at("8.1", 2.9))
    s.add(arrow(400, GREY, direction="l"), 760, 712, s.at("8.2", 0.0), anim="fade")
    node("credit", s.at("8.2", 0.4))
    s.add(arrow(110, GREY, direction="u"), 395, 548, s.at("8.2", 2.4), anim="wipe")
    node("brief", s.at("8.2", 2.7))
    s.add(arrow(110, GREY), 630, 285, s.at("8.2", 3.4), anim="wipe")
    s.add(circle(250, LIGHT, "Agent decides again", 32, NAVY, outline=NAVY, width=4), 960, 520, s.at("8.2", 3.8), center=True)
    s.add(box(820, 92, ORANGE, "15% control calls measure real uplift", tsize=38), 960, 885, s.at("8.3", 0.0), center=True, anim="up")
    return s


def scene9(t0, rows):
    s = Scene(t0, "What's Next", ["9.1", "9.2"], rows)
    cut = s.at("9.2", -0.1)
    s.els[0].t1 = cut - 0.35
    T = [("Objective", "meeting, enrichment or NPS", TEAL), ("Call time", "when the seller answers", ORANGE),
         ("Language", "suggested from the seller's data", PURPLE)]
    for i, (h, sub, col) in enumerate(T):
        s.add(box(520, 240, col, h, sub, tsize=52, ssize=32), 120 + i * 580, 380, s.at("9.1", 0.2 + i * 0.5), until=cut - 0.35)
    s.end += 1.5
    s.add(text("Persona Design", 120, NAVY), 960, 420, s.at("9.2", 0.2), center=True)
    s.add(text("A different conversation for every seller, and a system that learns from every call.", 40, GREY, bold=False,
               maxw=1500), 960, 570, s.at("9.2", 0.9), center=True, anim="up")
    for e in s.els[-2:]:
        e.t1 = None          # the last card stays to the final frame
    return s


SCENES = [intro, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, help="render one scene (0 = intro)")
    ap.add_argument("--preview", action="store_true", help="also save a JPEG every second")
    a = ap.parse_args()
    rows = beats()
    os.makedirs(OUT, exist_ok=True)
    t, built = 0.0, []
    for i, fn in enumerate(SCENES):
        sc = fn(t, rows)
        built.append(sc)
        t = sc.end
    if a.only is not None:
        sc = built[a.only]
        for e in sc.els:
            e.t0 -= sc.t0
            if e.t1 is not None:
                e.t1 -= sc.t0
        out = os.path.join(OUT, f"scene{a.only}.mp4")
        render(sc.els, sc.end - sc.t0, out, BG, preview_every=30 if a.preview else None)
    else:
        out = os.path.join(OUT, "vani_persona_pitch.mp4")
        render([e for sc in built for e in sc.els], t, out, BG, preview_every=30 if a.preview else None)
    print(out, f"{(built[a.only].end - built[a.only].t0) if a.only is not None else t:.1f}s")
    for sc in built:
        print(f"  {sc.title or 'intro':34s} {sc.t0:6.1f} -> {sc.end:6.1f}")


if __name__ == "__main__":
    main()
