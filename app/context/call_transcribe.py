"""Transcribe call recordings with Sarvam REST speech-to-text (voice use only).

Reads data/call_audio/picked.json (made from Call_Logs_Hackathon.csv), splits each mp3
into <= 25 s WAV chunks (Sarvam live STT limit is 30 s), transcribes with saarika:v2.5,
writes data/call_audio/<callNN>.json and prints seconds + cost estimate.
Key from env SARVAM_API_KEY only.   Run: python app/context/call_transcribe.py 4 3
"""
import io, json, os, sys, time, wave
import requests, soundfile as sf

D = os.path.join(os.path.dirname(__file__), "..", "..", "data", "call_audio")
CHUNK = 25  # seconds


def chunks(path):
    data, sr = sf.read(path, dtype="int16")
    n = int(CHUNK * sr)
    for i in range(0, len(data), n):
        b = io.BytesIO()
        with wave.open(b, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data[i:i + n].tobytes())
        yield i / sr, b.getvalue()


def stt(key, wav, model="saarika:v2.5"):
    r = requests.post("https://api.sarvam.ai/speech-to-text", headers={"api-subscription-key": key}, timeout=90,
                      files={"file": ("c.wav", wav, "audio/wav")}, data={"model": model, "language_code": "unknown"})
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} {r.text[:200]}")
    return r.json()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    key = os.environ["SARVAM_API_KEY"]
    pick = {p["n"]: p for p in json.load(open(os.path.join(D, "picked.json"), encoding="utf-8"))}
    total = 0.0
    for n in map(int, sys.argv[1:]):
        p, segs, t0 = pick[n], [], time.time()
        for start, wav in chunks(p["file"]):
            j = stt(key, wav)
            segs.append({"start_sec": round(start, 1), "text": j.get("transcript", ""), "language": j.get("language_code")})
        sec = p.get("sec") or sf.info(p["file"]).duration
        total += sec
        out = {"n": n, "remark": p["disposition_remarks"], "seconds": round(sec, 1), "chunks": len(segs), "segments": segs,
               "stt_wall_sec": round(time.time() - t0, 1)}
        json.dump(out, open(os.path.join(D, f"call{n:02d}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"call{n:02d} [{p['disposition_remarks']}] {sec:.0f}s, {len(segs)} request(s), {out['stt_wall_sec']}s wall")
    print(f"audio seconds transcribed: {total:.0f}")
