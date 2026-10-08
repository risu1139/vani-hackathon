"""Spike 8: can a self-hosted Daytona sandbox reach Sarvam and OpenRouter? Creates and deletes a throwaway sandbox."""
import os
from pathlib import Path

from daytona import Daytona, DaytonaConfig

for line in (Path(__file__).resolve().parents[2] / ".env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

daytona = Daytona(DaytonaConfig(api_key=os.environ["DAYTONA_API_KEY"], api_url=os.environ["DAYTONA_API_URL"]))
sandbox = daytona.create()
try:
    for url in ["https://api.sarvam.ai", "https://apps.sarvam.ai", "https://openrouter.ai/api/v1/models", "https://pypi.org/simple/"]:
        r = sandbox.process.exec(f"curl -s -o /dev/null -m 15 -w '%{{http_code}} %{{time_total}}s' {url}", timeout=30)
        print(f"{url}: {r.result.strip() or r.exit_code}")
    r = sandbox.process.exec("python3 --version; pip --version", timeout=30)
    print(r.result.strip())
finally:
    sandbox.delete()
    print("sandbox deleted")
