# VANI explainer video: storyboard

3 min, 1920×1080, canvas + Playwright + FFmpeg; Sarvam Bulbul v3 voice-over; a few OpenRouter (openai/gpt-image-2) illustrations. Visual-first: ~15 words on screen per scene; detail goes in the voice-over. Build: `app/video/`. Aggregates only; example sellers are invented and labelled illustrative.

Do not show: voice changing mid-call (tone only), Jev/Cowork as running live in the call. Jev IS explained in the video (user, 2026-10-10) in its true role: "keyword tool decides mood in the call; Jev labels real calls BETWEEN calls and improves the keyword tool" (corrected 2026-10-10) (confirmed by deck session), "AI"/"bot" wording, a figure next to a named seller, "best time to call" (not wired).

Never say "laptop" on screen or in voice-over; say "inside IndiaMART" or "at call time". Narration draft (7 min, 9 scenes): `outputs/plans/video-story-and-narration.md` (deck session). Numbers source: doc v6.

Deck source: `outputs/plans/VANI_Persona_Design_Deck_v2_visual.pptx` (15 slides, speaker notes = narration; origin/main after cba7daa). Proposed mapping (pending user): Scene 1 ← slides 2+3 · 2 ← 4 · 3 traits/states (new) · 4 sandbox + skill (new) · 5 ← 5+6+7 · 6 ← 8+9+10 · 7 ← 11+12 · 8 ← 13+14.

## Scene 1: Problem (~25 s) — APPROVED

- On screen: "Problem 04 · Persona Design" / "Same voice. Every seller. Whole call." / "21% of calls: seller in a rush → meetings halve"
- Visual: Context (seller cards with data chips) → GAP ← Objective (🤝 meeting with an IndiaMART executive). Old VANI sends one flat grey wave to all; rushed card flashes red, wave unchanged; crack labelled GAP; bridge "Persona" snaps in at the cut.
- Numbers: 11.5% of 269,455 answered calls (1 Apr–30 Sep 2026) end in a meeting. Rush signal in 21.0% of 11,834 transcribed calls: meetings 13.6% vs 26.0% without (keyword method, approx.).
- Voice-over: as in the doc text for Slide 1 (Context / Objective / Problem today / Challenge).

## Scene 2: Rich context, zero PII (~30 s) — APPROVED

- On screen: "62 data points per seller · ~60 sources" / "🔒 No personal data reaches the persona model"
- Visual: 8 tiles orbit one seller card — Business profile 91%, Catalogue 93%, Buy leads 100%, Enquiries 96%, Competitors (5–10 nearby same-category sellers, 15/15), Past VANI calls (0–21), Phone/WhatsApp/chatbot 79%, Identity/language/executive/account health 76%. Eight hook icons light up from their tiles. Tiles pass a 🔒 shield: names → {TOKEN}s, phone/email/GST/PAN/Aadhaar/address dropped; clean data → persona model; side arrow "names filled back on IndiaMART side" → Sarvam voice only. Grey "VANI today" box: no tile connects.
- PII claim (verified): "No real seller, buyer, competitor or staff name, phone number, email, GSTIN, PAN, Aadhaar, IFSC, pincode, address or GPS location reaches the persona model." Enforced by `app/persona/export_for_agent.py` (tokens + hard gate) and `app/daytona/deploy.py` leak_scan.
- Voice-over: "For each seller, we collect 62 data points from about 60 IndiaMART sources. Their business. Their catalogue gaps. Live buy leads. Their competitors. How past calls went. Each data point gives VANI a reason for the meeting. Before the model sees the data, we remove all personal data. Names become tokens. Phone, GST and PAN numbers never leave IndiaMART."
- Sources: seller-data-rebuild-redshift session (15 exports, 2026-10-10); `outputs/seller-md-field-inventory.md`.

## Scene 3: What traits and states are, and why (~32 s) — PROTOTYPE RENDERED (concept only; technical detail comes in later scenes)

Style: 3Blue1Brown-like (dark background, serif type, colour-coded ideas, shapes turn into one another). Prototype: `app/video/scenes/traits_states.html` → `app/video/build/traits_states/traits_states.mp4` (silent, 32 s).

- Beat 1 (0–6 s): Objective written on screen: "Turn raw seller data into facts a persona can reason with." It then shrinks to a header.
- Beat 2 (2–8 s): a cloud of 62 grey dots = "62 raw data points"; the cloud fades, 6 dots park on the left.
- Beat 3 (7–14 s): a time axis (0–120 days) draws. Three dots turn blue and stretch into flat lines: business size, division, language = "Traits: stable for months".
- Beat 4 (14–21 s): three dots turn yellow, each in its own lane: an event spike, then a curve that halves every 30 days: buy-lead use, call mood, enquiry flow = "States: change, and fade with time". A dashed marker shows "half after 30 days".
- Beat 5 (21–27 s): a green "today" line sweeps right and reads each line: traits stay the same, states are big when recent, small when old = "Recent signals count more. Old signals count less."
- Beat 6 (27–32 s): two cards: Traits = who the seller is · States = what is happening now. "Same data in → same facts out. Every time. Calculated by code. No guessing."
- Voice-over (approved first part): "Raw data is not a persona. First, code converts the data into facts. Stable facts are traits: business size, division, language. Changing facts are states: buy-lead use, enquiry flow, mood on recent calls." + (draft) "Recent signals count more; old signals fade. The same data always gives the same facts."
- Why we do it (reasoning to say): traits choose the base persona (who to be); states choose today's hook and tone (what to say now); decay stops an old mood deciding today's call; deterministic code makes every fact repeatable, testable and explainable before any model judges.
- Sources: `.claude/skills/vani-persona/scripts/facts.py` (13 traits, 15 states, half-lives mostly 30 d), `outputs/persona-hierarchy.md` §4–5.

## Scene 4: A persona for each seller (~35 s) — DRAFT

- On screen: "7 personas · 8 hooks · every choice cites seller data"
- Visual, beat 1 (library): 7 persona cards fan out — P0 VANI default (control) · P1 Numbers-first advisor · P2 Warm local helper · P3 Patient guide · P4 Brief and busy-friendly · P5 Respectful problem-solver · P6 Respectful senior advisor. Each card shows 3 dials: pace, warmth, formality.
- Beat 2 (selection): seller traits and states (division, turnover, AOV, city tier, language, call mood, buy-lead usage) flow in → two cards rise as top-2 → the persona agent picks one and tunes it from a fixed menu (pace_down, warmer, briefer, language_switch…). Each choice gets a small "cite" tag pointing to a data tile.
- Beat 3 (distinctness, 3 illustrative sellers side by side, invented):
  - small-town Gujarat trader, free, weak catalogue → P2 Warm local helper · Gujarati · slower · hook: profile gap
  - often-rushed Delhi distributor → P4 Brief and busy-friendly · Hinglish · fast, ≤12 words · hook: money lead
  - 5 Cr+ Pune manufacturer → P6 Respectful senior advisor · English-heavy · hook: peer usage
  Same objective under all three: 🤝 meeting.
- Guardrail strip at bottom: "Changes delivery. Never facts, prices or compliance."
- Voice-over (draft): "We do not use one script. For each seller, our persona agent reads the data and picks from seven persona styles. It then tunes pace, warmth and language for this seller. Every choice cites the seller data. The hook also comes from the data: a gap in the catalogue, a live buyer, or what similar sellers do. The persona changes how VANI speaks. It never changes facts or prices."
- Source: `outputs/persona-hierarchy.md` §7, §8, §10. Note: scoreboards are empty today (seed leans + random draw), so do not claim learned results.

---

# Storyline v2 (short) — for approval before any render

## Scene 1: The gap (~25 s)

| Voice-over | Viewer sees |
|---|---|
| IndiaMART knows a lot about each seller. Business, categories, past calls. | Seller cards appear; small data icons attach to each card. |
| Every call has one objective: a meeting with an IndiaMART executive. | One 🤝 meeting icon on the right. |
| But today, VANI speaks to every seller in the same voice and the same style, for the full call. | One grey sound wave goes, identical, to every card. |
| When a seller is in a rush, VANI does not change. | One card turns red ("rush"); the wave stays the same. |
| In these calls, meetings fall by half. | Big number: 26% → 14%. |
| We close this gap with a persona for each seller. | A bridge labelled "Persona" joins seller cards to the meeting. |

## Scene 2: Rich context, no personal data (~25 s)

| Voice-over | Viewer sees |
|---|---|
| For each seller, we read 62 data points. | One seller card in the centre; "62" counts up. |
| Their business. Their catalogue. Live buy leads. Their competitors. How past calls went. | Five icons fly in around the card, one per word. |
| Each one gives VANI a reason to meet. | Lines glow from each icon to the 🤝 meeting icon. |
| Before the model sees anything, personal data is removed. | Icons pass through a 🔒 shield. |
| Names become tokens. Phone, GST and PAN never leave IndiaMART. | Names turn into {TOKEN}; phone/GST/PAN icons drop away. |

## Scenes 1–2 build status (2026-10-10)

- Voice: Sarvam Bulbul v3, speaker **aditya** (male, deep), en-IN; chosen by user from varun/aditya/kabir/rahul samples. Lines spelled for speech ("Vaani", "sixty-two", "G S T").
- Shortened lines (user OK): 3 "But today, Vaani speaks to every seller the same way, for the whole call." · 8 "Business. Catalogue. Buy leads. Competitors. Past calls." · 11 "Names become tokens. Phone, GST and PAN stay inside IndiaMART."
- Output: `app/video/build/scene12/scene12_voice.mp4` (51.5 s, voice only, no music yet). Beats timed to each voice line; Whisper check: every beat's first word within 0.1 s of its animation (beat 8: 0.35 s).
- Pipeline: `app/video/voice.py` (TTS per beat) → `app/video/mix.py` (beat lengths + voice track) → `app/video/render.mjs --durs=…` → ffmpeg mux.
