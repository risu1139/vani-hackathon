# Voice-over brief: outputs and success-metrics scenes (end of the video)

For the storyboard session (Sarvam voice-over). Scenes: `app/video/scenes/outputs.html` and `app/video/scenes/metrics.html`, silent renders in `outputs/video/VANI_outputs.mp4` and `VANI_metrics.mp4`. Place: your scenes → demo calls → **outputs** → **metrics**.

## Voice settings (same as scenes 1 to 3)
- Sarvam Bulbul v3, en-IN, speaker `shubh`, pace 0.85 (your `app/video/voice.py` defaults).
- One WAV per beat, then re-time each beat to its audio with `render.mjs --durs=...` (beat lengths from `mix.py`), then mux.
- Add these two scenes to `LINES` in `voice.py` as `"outputs"` and `"metrics"`.

## Spelling for speech (screen keeps normal spelling)
VANI → "Vaani"; 12,354 is spoken as "twelve thousand"; 26% and 14% as "twenty-six percent" and "fourteen"; "0.9 ms" as "under a millisecond"; "Claude" as written; "Sarvam" as written.

## Lines

### outputs (6 beats, base 26 s)
| Beat | Base s | Voice line (as spoken) |
|---|---|---|
| 1 | 4.5 | Here is what we deliver for every seller. |
| 2 | 4.5 | A persona spec: every field has a value, and the seller's own data behind it. |
| 3 | 4.5 | A call plan, with a main reason to meet and a backup. |
| 4 | 4.5 | The live Sarvam agent, and a log of every switch it made, on the same turn. |
| 5 | 4.0 | After every call, Claude checks compliance and whether the persona fit. |
| 6 | 4.0 | And scoreboards that learn which persona works for which sellers. |

### metrics (8 beats, base 35.5 s)
| Beat | Base s | Voice line (as spoken) |
|---|---|---|
| 1 | 4.5 | How do we know it works? We measure five things. |
| 2 | 4.5 | Fit: all nine personas passed the validator, and every field quotes its reason. |
| 3 | 5.0 | Switches: every scripted switch landed on the same turn, decided in under a millisecond, with a reply in under a second. |
| 4 | 4.5 | Distinct: eight sellers got six different personas, in four languages. |
| 5 | 4.0 | Natural voice in Marathi, Hindi, English and Telugu, with live switching. |
| 6 | 4.5 | Evidence: built on twelve thousand past calls, and each persona quotes the seller's own history. |
| 7 | 4.5 | The biggest gap is rushed sellers: twenty-six percent meetings drop to fourteen. Now they get a brief persona. |
| 8 | 4.0 | And it gets better with every call. |

## Facts behind the lines (all measured; source `outputs/plans/success-metrics-data.md`)
- 9 of 9 persona runs passed the validator (sandbox and again outside it); every field has a reason (33 from seller data, 57 persona default).
- 15 scripted scenario calls: every intended switch on the same turn; signal tool median 0.91 ms; agent reply 0.92 s average per turn.
- 8 sellers → 6 personas (P0, P1, P2, P3, P4, P6), 4 languages.
- 20 calls: Marathi 12, Hindi 3, English 2, Telugu 2; mid-call switches into Hindi, English, Telugu (Gujarati in an earlier suite).
- 12,354 transcribed calls; 19 persona decisions cite the seller's own past call.
- Rushed vs not rushed: about 14% vs 26% meetings (11,834 transcribed calls, keyword method).

## Rules
Only measured numbers; no "projected" claims. Never say "laptop", "AI" or "bot" for VANI. Jev works between calls; the keyword tool decides in the call.
