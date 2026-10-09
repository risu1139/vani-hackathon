# Jev latency floor (2026-10-09)

Laptop over VPN, OpenRouter Decisions API, one warm keep-alive session, 8 calls each. Model typesafe/jev-1.13-20260917, provider TypeSafe.

| measure | median | min | max |
|---|---|---|---|
| network round trip (401 reply, same warm connection) | 26 ms | | |
| 1 question, seller turn only | 531 ms | 468 | 844 |
| 6 questions, agent line + seller turn | 476 ms | 450 | 515 |

- Network is about 26 ms, so **about 450–500 ms is Jev's own processing at TypeSafe**. Fewer questions doesn't make it faster: 6 questions took no longer than 1.
- Cost is about $0.000018 per call (419 input tokens).
- Vercel AI Gateway lists the same model (`typesafe-ai/jev`, `POST /v1/decisions`, questions as an array, type `predicate|choice|score`). It refused calls (403) until a credit card is on file, so it was not timed. It routes to the same TypeSafe provider, so the same ~450 ms floor is expected (ASSUMED).
