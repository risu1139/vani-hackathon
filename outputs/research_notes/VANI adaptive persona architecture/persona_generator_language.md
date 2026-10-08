# Persona Generator and Language Fit for an Indian B2B Seller-Calling Voice Bot (VANI PS07)

As of 2026-10-07. Tooling limited to Sarvam (Bulbul TTS, Saaras STT, Sarvam LLMs / Indus agents), OpenRouter models, and open-source. Internal findings are cited to local files (aggregate numbers only, no customer data). Sources older than 2026 are flagged.

Local sources:
- INT-VAL = `C:\Users\Imart\Voice ai hakethon\wiki\projects\vani-hackathon\persona-data-validation.md`
- INT-DICT = `C:\Users\Imart\Voice ai hakethon\raw\hackathon\2026-10-07-ps07-persona-data-dictionary.md`

---

## Q1. Bulbul V4: what is new vs V3, and which speakers fit warm/patient vs crisp/fast personas?

### Takeaway
Bulbul V4 launched 30 Jul 2026 at Sarvam Epoch with steerable emotion, emphasis, pacing and non-verbal cues such as laughter, across the same 11 languages as V3. The API identifier seen in integrations is `bulbul:v4-flash`. V3 is still the documented default, and the public TTS reference page still lists only v2 and v3. So V4-specific speaker IDs and control syntax must be confirmed in the dashboard before the demo. Pace (0.5–2.0) is the reliable persona lever. Pitch is not available on V3, while V4-flash reportedly restores pitch and loudness.

### Cited Findings
- Bulbul V4 was published on 30 Jul 2026, during the Builder Edition of Sarvam Epoch. — [AlphaSignal](https://alphasignal.ai/news/sarvam-ai-ships-bulbul-v4-to-bring-emotional-voice-to-11-indian-languages); [explainx (secondary)](https://explainx.ai/blog/sarvam-bulbul-v4-tts-emotion-voice-july-2026)
- Sarvam's own summary: "Developers can shape how each line is spoken, guiding emotion, emphasis, pacing, and cues such as laughter." It is positioned for voice agents where "names, amounts, product terms, and tone must be delivered clearly and accurately". No voice count, latency or V3 comparison is given. — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary)
- Secondary reporting: 11 languages (hi, bn, ta, te, gu, kn, ml, mr, pa, od, en-IN), "39 named voices", pace 0.5x–2.0x, "sub-250ms streaming latency", and consent-based voice cloning from 30–60 s samples. V4 pricing was not separately listed (V3 costs ₹30 per 10K chars). — [AlphaSignal](https://alphasignal.ai/news/sarvam-ai-ships-bulbul-v4-to-bring-emotional-voice-to-11-indian-languages). This is not confirmed on docs.sarvam.ai.
- The official sarvam-mcp PR adding `bulbul:v4-flash` says "pitch, loudness, and pace are now consistently supported, with pace enforced between 0.5–2.0". It mentions "224 v4-flash speakers" (probably speaker × language combinations; unverified), says "model-specific speakers and improved voice controls", and notes "The default remains Bulbul v3". — [sarvamai/sarvam-mcp PR #92](https://github.com/sarvamai/sarvam-mcp/pull/92)
- Bolna (an open-source voice-agent framework) registers `bulbul:v4-flash` with a native 22,050 Hz rate and streams it the same way as v3 (WAV header followed by raw PCM). — [bolna PR #1060](https://github.com/bolna-ai/bolna/pull/1060)
- **Conflict:** the official TTS API reference currently lists only `bulbul:v3` ("30+ voices, and temperature control") and `bulbul:v2` ("pitch and loudness controls"). On V3, pitch and loudness are listed as not supported. Pace is 0.5–2.0, temperature 0.01–2.0 (default 0.6), `dict_id` is a pronunciation dictionary (v3 only), and no emotion or style parameters are documented. — [Sarvam TTS convert API](https://docs.sarvam.ai/api-reference-docs/text-to-speech/convert.md); [Bulbul model page](https://docs.sarvam.ai/api-reference-docs/getting-started/models/bulbul)
- V3 speakers: shubh (default), aditya, ritu, priya, neha, rahul, pooja, rohan, simran, kavya, amit, dev, ishita, shreya, ratan, varun, manan, sumit, roopa, kabir, aayan, ashutosh, advait, anand, tanya, tarun, sunny, mani, gokul, vijay, shruti, suhani, mohit, kavitha, rehan, soham, rupali. Sample rates are 8/16/22.05/24 kHz (REST also supports up to 48 kHz). The docs do not give speaker genders. — [Bulbul model page](https://docs.sarvam.ai/api-reference-docs/getting-started/models/bulbul)
- V2 (legacy) speakers have documented genders (female: anushka, manisha, vidya, arya; male: abhilash, karun, hitesh). V2 pitch ranges from −0.75 to 0.75 and loudness from 0.3 to 3.0. — [Sarvam TTS convert API](https://docs.sarvam.ai/api-reference-docs/text-to-speech/convert.md)
- Bulbul V3 (blog of 7 Feb 2026) reportedly beat ElevenLabs and Cartesia Sonic-3 in a blind listening study with more than 500 annotators and about 20K votes across 11 languages. — [AlphaSignal](https://alphasignal.ai/news/sarvam-ai-ships-bulbul-v4-to-bring-emotional-voice-to-11-indian-languages); [Sarvam blog index](https://www.sarvam.ai/blogs)
- In the Sarvam agent platform, the "Per-language voices" mode maps a voice to the *starting* language and keeps it for the whole call, even if the caller switches. — [Sarvam conversation settings](https://docs.sarvam.ai/conversations/build/conversation-settings.md)

### Inferences
- Use **pace**, plus V4 emotion steering if verified, as the main live lever. Do not change the speaker mid-call: the platform fixes the voice per call, and a voice change mid-call sounds like a handoff.
- Suggested mapping, to be validated by ear in the Sarvam playground. Speaker genders are inferred from Indian name conventions and are not documented by Sarvam:
  - Warm/patient: a female speaker (e.g. ritu, priya, kavya) at pace 0.9–0.95, temperature around 0.5–0.6.
  - Crisp/fast (rush signal): a male speaker (e.g. shubh, aditya, rahul) at pace 1.1–1.2, temperature around 0.4 for steadier delivery.
  - Formal/senior: pace 0.95–1.0, low temperature.
- Pick a regional speaker per language by listening: names like gokul, mani, vijay and kavitha may have been recorded with Tamil or South Indian prosody, but this is unconfirmed.
- The deck must say "pace + emotion steering". It must not claim "pitch control" unless V4-flash pitch is verified on the platform, because pitch only exists on v2/v4-flash.

### Gaps
- No official V4 docs page was found listing V4 speaker IDs, gender, emotion-tag syntax, or pitch range. The "39 voices" and "224 speakers" figures conflict.
- No per-language MOS or naturalness scores for V4 were found.

---

## Q2. Saaras V4: code-mix, romanized vs native output, and keyterm prompting

### Takeaway
Saaras V4 (blog dated 25 Sep 2026) covers 22 Indic languages plus English and auto-detects the language. It offers five output modes from one model: transcribe, translate, verbatim, translit (fully romanized) and codemix (native script with English words kept in Latin script). Keyterm prompting accepts up to 50 terms of up to 64 chars each. Because internal seller turns are romanized (0.2% Devanagari, INT-VAL), the **translit** mode best matches existing analytics and evaluator inputs. Keyterms work best in *native script plus a language code*.

### Cited Findings
- V4 is the current recommended version. It supports Indian and global English plus 22 Indic languages with automatic language detection. Keyterm prompting (up to 50 terms) is V4 only and is "Available on REST and Batch APIs". V3 is still supported on all endpoints. — [Saaras model page](https://docs.sarvam.ai/api-reference-docs/getting-started/models/saaras)
- Modes: Transcribe (native script, normalized numbers), Translate (to English), Verbatim (keeps fillers), Translit (Roman script), Codemix (English words in Roman, other words in native script). — [Saaras model page](https://docs.sarvam.ai/api-reference-docs/getting-started/models/saaras)
- The release blog (25 Sep 2026) says V4 is "robust to noisy audios and code mixing" and "handles dialectical variation". Translit is "the whole utterance in English script". Streaming time-to-first-token is under 150 ms. — [Sarvam blog: Introducing Saaras V4](https://www.sarvam.ai/blogs/introducing-saaras-v4)
- Keyterm limits are 50 terms, each up to 64 chars. On AI4Bharat IndicContextEval (Interspeech 2026), V4 had the lowest WER, 16.03%, in the L5 setting, where the entity list was supplied in native script with the language. — [AnalyticsInsight](https://www.analyticsinsight.net/artificial-intelligence/sarvam-ai-saaras-v4-how-the-multilingual-speech-model-is-built-for-indias-diverse-languages); [Sarvam blog](https://www.sarvam.ai/blogs/introducing-saaras-v4)
- Architecture: an audio encoder plus Sarvam-3B, a hybrid state-space LM. — [AnalyticsInsight](https://www.analyticsinsight.net/artificial-intelligence/sarvam-ai-saaras-v4-how-the-multilingual-speech-model-is-built-for-indias-diverse-languages)
- Epoch summary: single-pass multi-speaker ASR (diarisation plus transcription), and lowest average WER on Indian-accented English benchmarks (LibriSpeech, GigaSpeech, Svarah). — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary)
- Internal: seller turns in transcripts are romanized (0.2% Devanagari). — INT-VAL

### Inferences
- Live pipeline: run Saaras V4 in **translit** mode for the reply LLM and signal detector, so it matches how training and evaluation data look. Optionally run **codemix** in parallel for the language-ID signal, since the native script reveals which language was spoken.
- Keyterm list (at most 50): "IndiaMART" in Latin plus native forms (e.g. इंडियामार्ट, இந்தியாமார்ட்), product and service names (e.g. "TrustSEAL", "Buy Leads", "catalog"), and the seller's own top_category_1..3 names, filled per call from seller data.
- Keyterm prompting is listed for REST and Batch only. Check whether the streaming or agent-platform STT exposes it. If not, apply post-ASR fuzzy correction against the same list (open-source rapidfuzz).

### Gaps
- No per-language WER for Tamil, Gujarati, Telugu, Kannada, Marathi or Bengali on 8 kHz telephony audio was found. Benchmark this on the 5,000-call recording sample (INT-DICT, file 5), which has 2,494 calls with existing transcripts to compare against.

---

## Q3. Persona spec schema mappable onto Sarvam agent settings

### Takeaway
The persona should be a compact JSON object. Platform-level fields (voice, start language, allowed languages, eagerness, temperature, interruption) map one-to-one onto Sarvam conversation settings. Behavioural fields (formality, warmth, Hinglish ratio, objection playbook, escalation and guardrails) render into the per-language system prompt and variables.

### Cited Findings
- Sarvam agent settings include:
  - Starting language, which can be overridden per contact in campaigns.
  - "Switch language during call" (smart language switch), "Languages allowed", and auto-detected switching with a configurable delay.
  - "Per-language voices", fixed for the call by starting language.
  - Model temperature from 0.1 ("Compliant") to 0.9 ("Creative"), default 0.3.
  - "Let callers interrupt" with two sensitivity controls, and "Eagerness to respond" (Patient/Normal/Eager).
  - Nudge messages for silent callers, numbers in Indic, voicemail with variables, and template variables such as `{{user_name}}`.
  — [Sarvam conversation settings](https://docs.sarvam.ai/conversations/build/conversation-settings.md)
- Per language, you can customise the prompt, agent name, handoff message and TTS/STT. — [Sarvam docs via search summary](https://docs.sarvam.ai/conversations/quickstart.md); compare the open-source [Bolna multilingual config](https://www.bolna.ai/docs/customizations/multilingual-config-reference)
- Indus Voice Agents is generally available at ₹3.50/min, with authoring, simulation and analytics. — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary)
- Available inputs are profile, engagement (`eng_*`, about 64% of sellers), and bot call history including past_objections, past_questions_asked, asked_if_talking_to_bot, showed_frustration, already_in_touch_with_executive and do_not_call_requested. — INT-DICT

### Proposed schema (inference; value sets kept small for distinctness and auditability)
| Field | Values | Sarvam mapping |
|---|---|---|
| `archetype` | one of 4–6 IDs (see Q5) | label only |
| `start_language` | hi-IN (Hinglish), ta-IN, gu-IN, te-IN, kn-IN, mr-IN, bn-IN, ml-IN, pa-IN, od-IN, en-IN | Starting language (per-contact override) |
| `allowed_languages` | start_language + hi-IN + en-IN | Languages allowed + smart switch ON |
| `hinglish_ratio` | low (~10% English) / medium (~30%) / high (~50%) | prompt instruction |
| `script_out` | native / romanized for TTS input | prompt plus TTS text normalisation |
| `voice` | speaker_id per language, gender ∈ {f, m} | Per-language voices |
| `pace` | 0.9 / 1.0 / 1.15 (start); live range 0.85–1.25 | TTS pace |
| `emotion` | calm / warm / upbeat (V4 only) | V4 control (verify syntax) |
| `eagerness` | patient / normal / eager | Eagerness to respond |
| `formality` | aap-formal / neutral / friendly-bhai-ji style | prompt |
| `warmth_empathy` | low / med / high | prompt plus emotion |
| `turn_length` | short (≤15 words) / medium | prompt |
| `opening` | 1 of ≤4 templated openings (kept minor) | initial message + variables |
| `objection_playbook` | ordered list of objection IDs to response templates (Q7) | prompt section |
| `escalation` | conditions → callback / human handoff / end | handoff message + tools |
| `guardrails` | disclose_ai, dnc_exit, no_price_promises, max_retries | prompt + tool hooks |
| `live_rules` | signal → delta (e.g. rush → pace +0.15, turn_length short, offer callback) | runtime controller |
| `evidence` | per field: source feature(s) + rule ID / stat | for "support from past-call evidence" |
| `temperature` | 0.2–0.4 | Model temperature |

### Inferences
- Because the voice is locked per call, the pre-call choices that cannot be undone are the speaker and the start language. Everything else (pace, eagerness, formality, language) should be live-adjustable.
- Keep an `evidence` field on every persona. It directly serves the judging criterion "support from past-call evidence".

### Gaps
- It is unclear whether the agent platform allows changing TTS pace or emotion mid-call via API or tool. If not, live pace changes need a custom pipeline (e.g. open-source Pipecat or Bolna with Sarvam services) instead of the hosted agent.

---

## Q4. Evidence on accommodation and persona matching in sales and service calls

### Takeaway
Evidence supports *matching pace and slowing slightly* (a satisfaction gain of about 7% in Wharton field and lab studies) and switching to the caller's language. Evidence that personalised *content* raises conversion is weak, and IndiaMART's own trials are 0 for 3. So the persona should change *how* the bot speaks (pace, language, brevity, empathy), not *what* it pitches.

### Cited Findings
- Wharton studies (hundreds of service calls plus five experiments) found that slowing articulation from 5.22 to 4.63 syllables/sec, still within the normal range, raised customer satisfaction by 7.1%. Slower speech within the normal range comes across as more empathetic, while extremely slow speech signals hesitation. (2025) — [Knowledge at Wharton](https://knowledge.wharton.upenn.edu/article/how-speaking-slower-influences-consumer-behavior/)
- Vocal parameters of the service agent relative to the customer (pitch, rate, amplitude) are associated with service-interaction outcomes. (2022, older) — [IDEAS/RePEc, IGI J. of Electronic Information Systems](https://ideas.repec.org/a/igg/jeis00/v18y2022i1p1-20.html)
- Industry claim, low-quality source without its own data: about 150 wpm is optimal on the phone, and agents who match the caller's pace get higher satisfaction. — [Ansafone/Anser Q&A](https://www.anser.com/qa/voicequality)
- Internal: static script personalisation failed in 3 trials:
  - `personalis`: 14.8% vs 17.8% meeting-fixed, p=0.13, but Not Interested fell from 13.1% to 5.5%.
  - `last_met_d`: 11.1% vs 15.8%.
  - `summary_va`: 3.3% vs 18.4%.
  — INT-VAL
- Internal live signals (keyword heuristic, 11,834 calls):
  - Rush appears in 21% of calls; meeting-fixed is 13.6% when present vs 26.0% when absent.
  - Frustration appears in 3.6%; 12.8% vs 23.8%.
  - Regional language appears in 2.3%; 31.4% vs 23.2%.
  - 68–99% of signals first appear mid-call.
  — INT-VAL
- Internal: 46.6% of Tamil Nadu calls carry Tamil markers, but the bot speaks Hinglish. — INT-VAL

### Inferences
- Communication Accommodation Theory predicts that convergence (rate, language) increases liking. The Wharton result plus the internal rush and regional signals make **live accommodation** the defensible thesis.
- Frame persona content changes as "earned attention" (lower NI%), and pair them with a stronger close (a concrete slot offer) rather than claiming lift.

### Gaps
- No peer-reviewed study was found on language-matching uplift for Indian outbound B2B voice bots specifically. Primary CAT call-centre papers (e.g. Giles et al.) were not fetched in this pass. The report should cite CAT generally or mark this as a gap.

---

## Q5. Persona generator design: rules vs LLM vs clusters vs uplift, and evaluating fit and distinctness

### Takeaway
Use a **hybrid**:
1. A deterministic rules layer for fields with hard evidence or compliance stakes: language, DNC, bot disclosure, escalation, and pace when frustration or rush was seen before.
2. A segment or archetype layer (clustering into 4–6 archetypes on validated drivers: turnover, business type, nature of business, engagement and history).
3. An LLM, via OpenRouter or Sarvam 105B, filling only the soft text fields (opening wording, playbook ordering, rationale) under a strict JSON schema, with an `evidence` citation per field.

Uplift modelling is the long-term policy, but there is no randomised persona data yet.

### Cited Findings
- Seller-trait spreads in meeting-fixed rate: turnover 9.7 pts (0–40 L converts best among known slabs), business type 7.1, nature of business 6.3, category group 3.8, state 3.3. Missing-profile sellers convert highest (~14–18%), which is a confound. — INT-VAL
- Sarvam 105B (conversational variant) scores 82.1 on voice-call, 63.4 on instruction following and 78.8 on tool calling, vs GPT 5.4 Mini (74.7/37.4/57.6) and Gemini 3.5 Flash (78.9/52.4/71.8), at $0.80 per million blended tokens. These are vendor-reported. Sarvam 30B/105B were open-sourced on 6 Mar 2026. — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary); [Sarvam blog index](https://www.sarvam.ai/blogs)
- Practitioner guide on building code-mixed LLMs (useful for Hinglish ratio prompting). — [Code Mixologist, arXiv 2602.11181](https://arxiv.org/pdf/2602.11181)

### Per-field rule vs LLM (inference, with reason)
| Field | Method | Reason |
|---|---|---|
| start_language | Rule: state/district lookup + past regional-language markers | strong internal signal (TN 46.6%); must be deterministic and auditable |
| voice gender/speaker | Rule per language + A/B | no evidence for gender effects; keep a fixed default per language to avoid confounds |
| pace / eagerness | Rule: showed_frustration or short avg_answered_call_sec → crisp; else default | rush and frustration halve meetings (INT-VAL) |
| formality | Rule: turnover slab + business_type (e.g. manufacturer/large → aap-formal) | turnover and business type are the largest spreads |
| hinglish_ratio | Rule: state (Hindi belt vs metro vs South) + past transcripts | measurable from past turns |
| opening | LLM from ≤4 templates | personalisation failed; keep it minor and templated |
| objection_playbook order | Rule: past_objections top-3 first; LLM phrases them | past objections are direct evidence |
| bot-disclosure prep | Rule: asked_if_talking_to_bot=1 → disclose up front | honesty and trust |
| escalation | Rule: already_in_touch_with_executive → route/confirm exec; DNC → do not call | compliance |
| rationale/evidence text | LLM | explanation for judges |

### Archetype starting set (inference, to be fitted by k-prototypes/k-means on the PS07 seller file)
1. Busy established manufacturer (high turnover, manufacturer): formal, crisp, pace 1.1, short turns, callback-first.
2. Small trader/retailer, newer GST: warm, Hinglish-high, patient, explain value.
3. Regional-language seller (TN/GJ/AP/KA/MH/WB): native-language start, Hinglish fallback.
4. Previously frustrated or bot-sceptic: up-front AI disclosure, very short turns, fast human-handoff offer.
5. Already-engaged with an executive: confirm the existing relationship, do not re-pitch.
6. Unknown/thin-profile: neutral default (this group converts highest, so do not over-adapt).

### Evaluating fit and distinctness (inference)
- **Fit:** an LLM-as-judge (an OpenRouter model different from the generator) scores each persona vs the seller features on a rubric, with an evidence check that each claimed field reason must cite an actual feature value. Human spot-check about 50 personas. Offline, compare persona choices against what worked in historical calls of similar sellers, e.g. did meetings occur when the past bot spoke the seller's language or the seller rushed.
- **Distinctness:**
  - Pairwise field-level Hamming distance across archetypes.
  - Silhouette score of the seller clusters.
  - Embedding cosine distance between rendered system prompts.
  - Acoustic distinctness: the pace and speaker difference audible in TTS samples.
  - Report a matrix of personas × fields.
- **Causal (future):** randomise persona arms and fit an uplift model (e.g. open-source CausalML/EconML T-learner) to learn the policy; personalisation trials show why claims need randomisation.

### Gaps
- No published 2025–26 case study on LLM persona generators for outbound voice bots with measured lift was found.

---

## Q6. Language selection policy and regional support quality

### Takeaway
Default the language from the state using a rule table, and override it with history if past transcripts show regional markers. Always allow Hindi/Hinglish and English as switch targets with auto-switch on. Bulbul covers 11 languages: Tamil, Telugu, Kannada, Malayalam, Gujarati, Marathi, Bengali, Punjabi, Odia, Hindi and English. Saaras covers 22, so STT can understand Assamese, Urdu and others that TTS cannot speak; fall back to Hinglish or English there.

### Cited Findings
- Bulbul (v3 and v4) languages: hi, bn, ta, te, gu, kn, ml, mr, pa, od, en-IN. — [Bulbul model page](https://docs.sarvam.ai/api-reference-docs/getting-started/models/bulbul); [AlphaSignal](https://alphasignal.ai/news/sarvam-ai-ships-bulbul-v4-to-bring-emotional-voice-to-11-indian-languages)
- Saaras covers 22 Indic languages plus English with auto language ID. — [Saaras model page](https://docs.sarvam.ai/api-reference-docs/getting-started/models/saaras)
- Platform: smart language switch, auto-detect with delay, and allowed languages; the voice stays fixed per starting language. — [Sarvam conversation settings](https://docs.sarvam.ai/conversations/build/conversation-settings.md)
- Internal:
  - Tamil Nadu has 46.6% Tamil-marker calls.
  - Gujarat is the second-largest state, but its 2% Gujarati-marker rate is understated because of a thin lexicon.
  - Regional-language calls show a 31.4% vs 23.2% meeting-fixed rate.
  — INT-VAL

### Policy (inference)
- State → default:
  - TN → ta-IN; GJ → gu-IN with Hinglish on standby.
  - AP/TS → te-IN; KA → kn-IN; KL → ml-IN; WB → bn-IN; OD → od-IN.
  - MH → Hinglish start (Marathi on switch; Mumbai/Pune are Hindi-heavy).
  - PB → Hinglish/pa on switch.
  - Hindi belt/NCR → Hinglish (medium-high English mix).
  - NE/others → Hinglish/English.
- For GJ/MH/KA metros with mixed populations, consider an opening in Hinglish plus one native-language greeting phrase, then switch on the first native reply.
- Live switch triggers:
  - Two consecutive seller turns detected in language X, with confidence above a threshold.
  - An explicit request ("Tamil-la pesunga", "Gujarati ma bolo").
  - Repeated confusion signal while in Hinglish → offer the regional language.
  - Do not flip on a single loanword (use the platform's switch delay).
- Script handling:
  - STT in translit for reasoning.
  - The LLM generates in the native script for TTS (Bulbul pronounces native script more reliably).
  - For Hinglish, generate Devanagari Hindi with English nouns in Latin.
  - Use Bulbul `dict_id` pronunciation dictionaries for "IndiaMART" and category names.
- Voice per language: one fixed speaker per language chosen by listening tests. Because the speaker is locked to the starting language, a mid-call switch keeps the original voice, so choose voices that sound acceptable across hi plus the target language.

### Gaps
- No independent per-language quality comparison for Bulbul V4 (Tamil vs Gujarati vs Marathi etc.) was found.
- The agent platform's language-ID accuracy on romanized code-mix is undocumented.

---

## Q7. Objection playbooks by seller segment (B2B tele-sales literature)

### Takeaway
Across 300M+ cold calls, objections fall into three types: dismissive (49.5%), situational (42.6%) and existing-solution (7.9%). The top 5 objections make up 74% of all objections. Handling follows three steps: agree, incentivise the conversation with a question, and sell the "test drive" rather than the full product. Map these onto IndiaMART's own past_objections categories per segment.

### Cited Findings
- Objection types and shares:
  - Dismissive (49.5%: "not interested", "call in 6 months", "send info", "where'd you get my number"): use disarming bluntness and agreement, then uncover the real concern.
  - Situational (42.6%: price, budget, bandwidth, fit): remove buying pressure and sell a pilot or test drive.
  - Existing solution (7.9%): agree, ask questions that expose limits, and give social proof. Criticising the incumbent makes prospects defensive.
  — [Gong Labs, 300M cold calls (pub. Jul 2024, updated May 2026)](https://www.gong.io/resources/labs/we-found-the-top-objections-across-300m-cold-calls-heres-how-to-handle-them-all/)
- The top 5 ("not interested", "too expensive", "send me an email", "no budget", "already have a solution") account for 74% of objections. — [Gong Labs](https://www.gong.io/resources/labs/we-found-the-top-objections-across-300m-cold-calls-heres-how-to-handle-them-all/)
- Internal categories exist (e.g. "Seller Unavailability & Scheduling Constraints"; question types Meeting Visit, Identity Confirmation, Pricing Payment), and the `objections` evaluator covers 5,233 calls with quotes. — INT-DICT

### Segment playbooks (inference)
- **Busy/rush (any segment):** acknowledge ("2 minute lunga"), offer a fixed callback slot, end early. Do not push through, because rush halves meetings.
- **Established manufacturer, high turnover:** existing-solution and price objections. Give peer proof from the same category and city, and offer a meeting as a no-commitment review.
- **Small trader/new seller:** situational price objections. Use the test-drive framing, a simple value story (enquiries/leads), and a patient tone.
- **Already in touch with an executive:** confirm the executive's name and offer to coordinate. Do not re-pitch.
- **Bot-sceptic/identity question:** disclose honestly, then give a crisp purpose and an offer of human callback.
- **Frustrated:** apologise once, give a short exit or callback, and log it for suppression.

### Gaps
- No India-specific B2B MSME objection-frequency study was found. Use the internal evaluator output instead.

---

## Q8. Guardrails: TRAI/DND, AI disclosure, do-not-call

### Takeaway
The TRAI TCCCPR amendment of Feb 2025 tightened consent, complaint windows (7 days) and mandatory designated number series (140/160) for commercial calls. AI-specific disclosure is under consideration but not yet codified. Design to the stricter standard anyway: always disclose when asked, and honour DNC immediately and persistently.

### Cited Findings
- The Feb 2025 amendment set a 7-day complaint window (up from 3), inferred consent valid only during the contractual relationship, explicit consent for a transaction valid 7 days, complaints allowed without DND registration, and mandatory designated numbering series for commercial calls. — [JSA Prism (Feb 2025, older)](https://www.jsalaw.com/wp-content/uploads/2025/02/JSA-Prism-Telecommunications_February-2025_TCCCPR-amendments.Final_.pdf); [Bar & Bench / S.S. Rana](https://www.barandbench.com/law-firms/view-point/trais-crackdown-on-spam-calls-and-ai-driven-telemarketing)
- 140-series telemarketing moved to a DLT blockchain platform. TRAI is "considering" amendments for AI-based telemarketing, AI disclosures and consent verification, and TCCCPR does not yet regulate AI as a risk category. — [Bar & Bench](https://www.barandbench.com/law-firms/view-point/trais-crackdown-on-spam-calls-and-ai-driven-telemarketing)
- TRAI press release No. 119 of 2026 (Sep 2026) exists, but its content could not be parsed. — [TRAI PR 119/2026](https://www.trai.gov.in/sites/default/files/2026-09/PR_No119of2026.pdf)
- Internal flags available: asked_if_talking_to_bot, do_not_call_requested, showed_frustration. — INT-DICT

### Inferences
- Hard rules outside the LLM:
  - do_not_call_requested=1 → never generate a persona or call.
  - A DNC phrase heard live → apologise, confirm and end, and write a suppression flag.
  - "Are you a bot?" → truthful answer ("Main IndiaMART ki AI assistant hoon"), with an offer of human callback.
  - No price or ranking promises, and no claims of being a human executive.
  - Maximum one retry per objection.
- Note: B2B transactional or service calls to existing paying sellers may fall under service rather than promotional categories. That is a legal question for IndiaMART compliance, not for the bot.

### Gaps
- The content of the Sep 2026 TRAI press release could not be read. Re-check whether it addresses AI calls before citing regulation in the deck.

---

## Q9. What the deck's success metrics need

### Takeaway
Each metric needs a concrete, measurable artifact. Lead with live adaptation and language fit, since the opening alone has failed.

### Cited Findings
- Personalisation failures and live-signal prevalence (see Q4). — INT-VAL
- Saaras V4 modes and benchmarks for language proof. — [Sarvam blog](https://www.sarvam.ai/blogs/introducing-saaras-v4)
- Bulbul languages and expressiveness. — [Sarvam Epoch summary](https://www.sarvam.ai/epoch/summary)

### Inferences
- **"Fit of each persona to its seller":**
  - Show a per-field evidence table (feature → rule → value).
  - Report an LLM-judge plus human rubric score.
  - Run a backtest: for sellers whose past calls showed rush, frustration or regional language, show that the persona pre-selects crisp, short or native-language settings, and that those signals correlate with outcomes (INT-VAL).
- **"Distinctness across seller types":**
  - Show a 5–6 archetype matrix with field-level Hamming distance and silhouette score.
  - Play side-by-side audio of the same line in 3 personas (pace and language differ).
- **"Natural voice in 2+ languages":**
  - Live demo in Hinglish → Tamil (and Gujarati) using Bulbul V4.
  - A small MOS panel of 5–10 native listeners rating 1–5.
  - Saaras WER on 20–50 regional clips from the recording sample.
- **"Support from past-call evidence":**
  - Cite aggregate stats: TN 46.6% Tamil; rush 21% of calls with meetings halved; turnover spread 9.7 pts.
  - Make every persona carry an `evidence` list referencing past_objections, past_questions_asked and flags.
  - State honestly that causality needs a randomised trial.

### Gaps
- No public rubric from IndiaMART judges was found beyond the four phrases given.
