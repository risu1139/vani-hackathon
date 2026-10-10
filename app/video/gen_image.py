"""Generate one illustration with an OpenAI image model via OpenRouter's images endpoint.

Usage: python app/video/gen_image.py <out.png> <prompt-file> [--model openai/gpt-image-2] [--size 1536x1024] [--quality high]
"""
import argparse, base64, json, os, requests

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("prompt")
ap.add_argument("--model", default="openai/gpt-image-2"); ap.add_argument("--size", default="1536x1024"); ap.add_argument("--quality", default="high")
a = ap.parse_args()
key = [l.split("=", 1)[1].strip().strip('"') for l in open(os.path.join(REPO, ".env"), encoding="utf-8") if l.startswith("OPENROUTER_API_KEY=")][0]
r = requests.post("https://openrouter.ai/api/v1/images/generations", timeout=600,
                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                  json={"model": a.model, "prompt": open(a.prompt, encoding="utf-8").read(), "size": a.size, "quality": a.quality, "n": 1})
if r.status_code != 200:
    raise SystemExit(f"{r.status_code}: {r.text[:500]}")
d = r.json()["data"][0]
img = base64.b64decode(d["b64_json"]) if d.get("b64_json") else requests.get(d["url"], timeout=120).content
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
open(a.out, "wb").write(img)
print("saved", a.out, len(img), "bytes")
