# Building and refining a library of VANI agent personas (voice + delivery + plan style)

Scope: VANI's *own* personas (voice/timbre, pace, pitch, formality, warmth, brevity, language mix, plan style), not seller types. As of 2026-10-09. Tags: DOCUMENTED (outside source), PROVEN (our data/spikes), ASSUMED (our inference). Binding frame: [PS04 doc](../../../raw/hackathon/2026-10-08-ps04-persona-design-problem-doc.md) — output is a persona *per seller* (FAQ Q1), so "library" here = a small set of **archetypes / building blocks** that the generator adapts per seller. Distinctness metrics are covered in depth in [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md); this note only adds the library angle.

## Q1. How do designers (expert-led) build agent personas, and how many do companies keep?

### Takeaway
Designer practice defines one persona as a short bundle of 4–6 trait adjectives, then auditions voices against those adjectives; the 2026 state of the art (Alexa+) has moved to a **small set (3–4) of named styles defined as levels on ~5 shared behavioural dimensions over one fixed capability/fact layer** — exactly the shape PS04 needs. Companies keep few personas because each must be consistent and auditable; variety comes from dimension levels, not from many characters.

### Cited Findings
- Google conversation design: brainstorm adjectives, "narrow your list down to 4-6 key adjectives", sketch candidate characters, pick one and write a ≤1-paragraph description; "avoid specifying things like gender or age because they almost never critically define or differentiate a persona" — DOCUMENTED — [Google: Create a persona](https://developers.google.com/assistant/conversation-design/create-a-persona)
- Google: choose the voice by an **audition** — rate candidate voices against the core adjectives on a 5-point scale, collect colleague feedback; voice must be "consistent with your persona". Page addresses a single persona only, nothing on multiple personas — DOCUMENTED — [Google: Create a persona](https://developers.google.com/assistant/conversation-design/create-a-persona)
- Amazon Alexa skills: in a VUI the tools are "voice, word choice, and sound effects"; their combination is the persona; users "paint a picture of the character in their minds"; a consistent persona "can increase conversion, engagement" (claim, no numbers given) — DOCUMENTED — [Alexa blog 2018](https://developer.amazon.com/en-US/blogs/alexa/alexa-skills-kit/2018/08/hear-it-from-a-skill-builder-how-to-create-a-persona-for-your-alexa-skill)
- Alexa+ personality styles (2026): **Brief** ("cuts straight to the point… no small talk"), **Chill** (easygoing, breezy), **Sweet** (warmth, enthusiasm), later **Sassy** (adult, wit). All styles are levels on five dimensions — **expressiveness (concise↔verbose), emotional openness (reserved↔enthusiastic), formality (professional↔casual), directness (diplomatic↔blunt), humour** — and the "same capable Alexa" stays unchanged; only communication style varies — DOCUMENTED — [About Amazon](https://www.aboutamazon.com/news/devices/alexa-plus-personality-styles); launch date reported as 25–26 Feb 2026 by [Dataconomy](https://dataconomy.com/2026/02/26/amazon-launches-new-alexa-ai-personality-styles-brief-chill-and-sweet/) vs "March 1, 2026" by [Storyboard18](https://www.storyboard18.com/digital/alexa-update-brings-three-new-tone-settings-as-amazon-expands-customisation-90908.htm) (minor conflict; Sassy added March 2026 per [Storyboard18](https://storyboard18.com/digital/amazon-unveils-sassy-mode-for-alexa-with-humour-and-explicit-language-92080.html))
- Foundational: Nass & Brave show people apply social rules (gender stereotypes, similarity-attraction, personality consistency between voice and words) to synthetic voices; mismatch between voice and content personality lowers liking/trust — DOCUMENTED (book) — [Wired for Speech, MIT Press 2005](https://mitpress.mit.edu/9780262640657/wired-for-speech/)
- Foundational: Cathy Pearl's VUI design text treats persona (voice, word choice, consistency) as a first-class design artefact for IVR/voice bots — DOCUMENTED (book) — [Designing Voice User Interfaces, O'Reilly 2016](https://www.oreilly.com/library/view/designing-voice-user/9781491955406/)
- Voice-vendor practice: A/B testing different voices for conversion is common; vendors report that male voices are perceived as more authoritative by some users and female as more empathetic by others, "varying by industry, audience demographics, and regional preferences" (vendor content, no data) — DOCUMENTED (weak) — [Cekura](https://www.cekura.ai/blogs/how-to-ab-test-voice-agents), [Regal](https://regal.ai/blog/a-b-tests-for-ai-voice-agent)
- Sarvam's own Bulbul v4 catalogue is already organised designer-style: each voice = adjectives (warm/confident/brisk/soft-spoken…) + pitch word (low/high) + pace word (slow/brisk/fast) + use case (Sales, Conversational, Customer Support) — PROVEN (our catalogue dump) — [catalogue](../../../raw/research/2026-10-07-sarvam-voice-catalogue.json)

### Inferences
- ASSUMED: The defensible structure is the Alexa+ shape: **persona = vector of discrete levels on fixed dimensions + a fixed fact/compliance layer**. PS04 already lists the dimensions (gender, accent, pitch, pace, Hinglish mix, formality, warmth/empathy, plan); we add brevity and directness (Alexa+ "expressiveness"/"directness"), which map onto rush and price-objection behaviour.
- ASSUMED: "How many?" — industry evidence points to **3–5 named styles** (Alexa+ 3→4). No source gives a principled count; the binding constraint for us is distinct voices per language in Sarvam (see Q4).
- ASSUMED: Google's "don't define by gender/age" supports letting voice gender be a *casting* choice tested by data, not something derived from seller demographics.

### Gaps
- Did not retrieve primary IBM or Microsoft bot-personality guidance in this pass; no evidence they differ materially from Google's adjective method.
- No public source states how many voice personas any Indian outbound-calling company (e.g., SquadStack) maintains.

## Q2. Data-driven methods: deriving, generating and testing agent styles

### Takeaway
Data-driven practice has four parts: (a) mine top human performers' behaviours (Gong/Cresta) to set dimension levels; (b) treat a persona as a factorial combination of levels and learn per dimension (Aampe-style Thompson sampling); (c) generate diverse candidates with LLM + quality-diversity archives and screen in simulation; (d) refine live with A/B/bandits. Effectiveness research on voice attributes is real but mostly lab-scale; in India the strongest documented driver of TTS preference is **expressiveness + intelligibility**, not gender.

### Cited Findings
- Gong Labs (recorded, transcribed calls mapped to CRM): top performers speak ~**171 wpm vs 182 wpm** for others; they shift the prospect's rate ~13% within 3 min (vs 7% for average reps) — they lead tempo rather than mirror it; prospects of top reps speak 174 vs 198 wpm — DOCUMENTED (Gong via aggregator; primary page [Gong Labs](https://www.gong.io/resources/labs/elements-of-effective-sales-conversations/), figures as quoted by [SalesLion](https://saleslion.io/sales-statistics/71-words-per-minute-the-surprising-speech-speed-of-top-performers-who-speak-6-slower-than-their-peers/)); B2B English sales, not Indian SMB
- Cresta: infers outcomes (sales, conversion, CSAT) from conversations and correlates them to specific behaviours to show "what top performers do differently", then pushes those behaviours via real-time hints; top performers follow hints ~20% more than bottom performers — DOCUMENTED (vendor) — [Cresta](https://cresta.com/blog/close-retention-performance-gaps-with-real-time-coaching)
- Aampe: per-user agents optimise separate dimensions (content, timing, frequency, channel) and compose messages modularly from tone, value proposition, incentive, CTA; uses a Thompson-sampling variant with beta posteriors from each user's response history — DOCUMENTED — [Aampe docs](https://docs.aampe.com/docs/core-concepts), [Aampe blog](https://aampe.com/blog/agentic-architecture-in-action-aampe-s-dual-path-personalization-strategy)
- Quality-diversity: MAP-Elites keeps an archive of the best solution per cell of a feature grid ("diverse and high-performing" rather than one optimum); LLMs can act as the mutation/generation operator over the archive (in-context QD), and QDAIF uses LM feedback both to score quality and to place outputs on diversity axes — DOCUMENTED — [LLMs as in-context QD generators, arXiv 2404.15794](https://arxiv.org/pdf/2404.15794), [MAP-Elites over prompt space, arXiv 2504.14367](https://arxiv.org/pdf/2504.14367), [QDAIF summary](https://hackernoon.com/quality-diversity-through-ai-feedback-approach)
- Persona collapse: LLM-generated persona populations converge into a few stereotyped modes; most faithful models are most stereotyped — DOCUMENTED — [arXiv 2604.24698](https://arxiv.org/abs/2604.24698) (detail in [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md))
- Voice-agent A/B: a voice agent is multi-turn and non-deterministic, so "a single run proves very little"; each scenario must be run several times and compared on a full metric set; bandits shift traffic to winners; variants commonly include "a different voice" — DOCUMENTED — [Cekura](https://www.cekura.ai/discover/how-to-ab-test-voice-agents), [Hamming](https://hamming.ai/resources/voice-agent-ab-testing-guide)
- Indian TTS preference at scale (Anand et al., Apr–Jun 2026): **120K pairwise comparisons, 1,900+ native raters, 10 Indic languages, 7 systems**, code-mixed sentences included; SHAP: "**Expressiveness and intelligibility are the strongest predictors of overall preference, followed by liveliness and voice quality**"; comparisons were done within the same gender to avoid gender confounds; Bulbul v3 Beta ranked 4th (52% win rate, 9 languages) and was noted for "comparatively lower expressiveness and liveliness"; Gemini 2.5 Pro TTS first in 9/10 languages — DOCUMENTED — [arXiv 2604.21481](https://arxiv.org/html/2604.21481)
- Accent: listeners showed the strongest positive social attitudes toward, and converged most to, Indian-English TTS voices (in that study's population) — DOCUMENTED — [Frontiers in Computer Science 2023](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2023.1204211/pdf)
- Voice attributes vs perceived personality (2025 studies): middle speech rate is the most influential element for perceived competence, high pitch least; gendered voices triggered stronger anthropomorphism and higher trust, broadly matching stereotypes (warmth↔feminine, authority↔masculine); gender-ambiguous voices polarised listeners — DOCUMENTED (small academic studies; search-snippet level, not fully read) — [IIS 2025](https://iacis.org/iis/2025/1_iis_2025_431-445.pdf), [TU Dresden](https://fis.tu-dresden.de/portal/en/publications/trust-in-gendered-voice-assistantsthe-special-case-of-gender-ambiguity(a28d4182-80d7-4895-8493-3211d7ba3f4f).html), [Essex thesis](https://repository.essex.ac.uk/41758/)
- Our past data (PS07) used ONE VANI voice/style, so it cannot rank voice personas; it does show which *delivery situations* matter: rush in 21% of transcribed calls (meeting rate 13.6% vs 26.0%), frustration 3.6% (12.8% vs 23.8%), Tamil markers in 46.6% of TN calls; three script-personalisation trials did not beat control — PROVEN — [persona-data-validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md)

### Inferences
- ASSUMED: For VANI the realistic data-driven seed is **"top-call mining" on PS07** instead of top agents: take meeting-fixed vs not calls within each seller segment and measure VANI-side delivery features that *did* vary despite one voice (reply length, turns before value statement, question count, Hinglish ratio, whether callback offered). These set brevity/plan-style levels; voice/pitch levels must come from design + catalogue + live testing.
- ASSUMED: The Gong result argues **against a "fast" persona as default**: even for busy sellers, the win is *shorter content and a callback offer*, not faster speech. Keep pace within ~0.9–1.1 and put the rush response into brevity.
- ASSUMED: The Indian TTS study argues that within a language the voice that sounds most **expressive and intelligible** beats subtler gender/pitch choices; so cast each archetype's voice by a quick audition on those two axes first.
- ASSUMED: Factorial view: 2 genders × 3 pace × 3 formality × 3 warmth × 3 brevity × 3 plan styles = 486 cells — far too many to test directly. Aampe-style per-dimension posteriors (assuming roughly additive effects) or a constrained QD grid (cells = audible dimensions only) make it tractable.

### Gaps
- No published study found on voice persona effects for **Indian B2B/SMB outbound calls** specifically (gender, pace, formality), nor any Hindi/Hinglish speech-rate-vs-conversion data.
- No public evidence that Cresta/Observe.AI cluster *agent styles* into named personas; their documented method is behaviour→outcome correlation.

## Q3. How is a persona library refined over time (versioning, keep/tune/drop/add, minimum data, stereotypes, distinctness)?

### Takeaway
Treat each archetype as a versioned artefact (voice id + dimension levels + plan template + reasons), give it traffic via a segment-aware bandit with a holdout, and apply explicit keep/tune/drop/add rules with minimum-sample gates; never condition voice gender (or other casting) on sellers' protected attributes, and audit outcomes by segment. Distinctness is kept by construction (archetypes must differ on ≥1 audible dimension) and checked with attribute- and audio-level metrics.

### Cited Findings
- UNESCO "I'd blush if I could" (2019): recommends stopping female-by-default assistants and discouraging gendered submissiveness; documented that female voices cluster in "household/help" roles and male in authority/navigation roles — DOCUMENTED — [CBS News](https://www.cbsnews.com/news/alexa-siri-other-artificial-intelligence-voice-assistants-gender-bias-unesco), [Open Access Government](https://www.openaccessgovernment.org/gender-stereotypes-in-ai/65868/)
- Gender-voice trust effects broadly follow stereotypes (warmth↔female, authority↔male) — so optimising purely for short-term response can *learn* stereotypes — DOCUMENTED — [IIS 2025](https://iacis.org/iis/2025/1_iis_2025_431-445.pdf)
- Thompson sampling with per-user beta posteriors is a production pattern for continuous per-dimension refinement — DOCUMENTED — [Aampe docs](https://docs.aampe.com/docs/core-concepts)
- Voice-agent experiments need canary gates and repeated runs per scenario before a change ships — DOCUMENTED — [Hamming](https://hamming.ai/resources/voice-agent-ab-testing-guide)
- Our design already ships updates only through a frozen-test-set gate (B11) and stores one append-only trace per run (B8) — PROVEN as design, build ASSUMED — [system-design](../../../wiki/projects/vani-hackathon/system-design.md)
- Distinctness metrics (per-dimension entropy/coverage, distinct-persona ratio, pairwise Hamming, Mantel correlation of seller distance vs persona distance, audio pace/pitch/speaker-embedding distance) — see [distinctness.md](../Self%20improving%20persona%20and%20switch%20loops/distinctness.md) Q3

### Inferences
- ASSUMED **versioning:** `archetype_id@vN` = {Sarvam agent version id, speaker, pace, pitch, levels on formality/warmth/brevity/directness/Hinglish, plan template id, rationale, evidence grade}. Any change to speaker/pace/pitch = new Sarvam published version; changes to wording/plan = new template version only (passed per call via variables — PROVEN that variables/opening/language work per call).
- ASSUMED **minimum data (computed):** PS07 meeting-fixed ≈11.5% overall (PROVEN). Detecting a 3-point absolute lift (≈13%→16%) at α=0.05, power 0.8 needs ≈2·(1.96+0.84)²·p(1−p)/d² ≈ **~2,000 calls per arm per segment**; a 5-point lift ≈ ~700. At 12-lakh-seller scale this is days of traffic for coarse segments, but impossible for fine per-seller cells → learn archetype × *coarse* segment (e.g., 6–10 segments), and personalise within the archetype with rules/memory, not with experiments.
- ASSUMED **keep/tune/drop/add rules:**
  - Keep: archetype is best or within the credible interval of best in ≥1 segment.
  - Tune: winning in a segment but losing on a secondary metric (e.g., more "Not Interested", longer calls) → change one dimension level, new minor version, paired test.
  - Drop: posterior P(best) <5% in every segment after the minimum sample, or fails the guardrail/compliance audit.
  - Split: high outcome variance inside an archetype that a seller feature explains (e.g., rush-prone vs not) → two archetypes, provided they differ on an audible dimension.
  - Add: new candidates proposed by LLM into *empty or weak QD cells* (cells = audible dimension combos), screened in simulation (B7) + judge, then given a small exploration share (e.g., 5–10%).
  - Merge: two archetypes whose measured audio features (wpm, F0, speaker embedding) and outcomes are indistinguishable.
- ASSUMED **stereotype guard:** (1) never use seller gender, religion, caste, or name-inferred ethnicity as inputs to voice choice; language comes from state/PNS/live switch (functional, not identity); (2) voice gender is balanced per archetype (each archetype has a male and female voice where the catalogue allows) and randomised/bandit-tested, not assigned by "warm = female, authority = male"; (3) report outcomes per region/language/turnover band and stop any arm whose lift comes only from a stereotyped mapping; (4) fixed guardrail: personas change delivery, never facts/pricing/compliance (FAQ Q5).
- ASSUMED **distinctness in the library:** each pair of archetypes must differ on ≥2 dimensions, at least one audible (speaker, pace, or brevity measured in words/turn); monitor that the per-seller layer does not drift all sellers into one archetype (archetype-share entropy).

### Gaps
- No public case study found of a company publishing its persona-library keep/drop rules; the rules above are our design.
- Effect sizes for voice persona changes in outbound calls are unknown, so the sample sizes are estimates under an assumed 3–5 pt lift.

## Q4. Concrete proposal for VANI: starting library, justification, Sarvam mapping, evolution; devil's advocate

### Takeaway
Start with **4 Hindi/Hinglish archetypes (≈4 published Sarvam versions) + 2 English + 1 Tamil**, each differing on voice and on at least one more audible dimension; the generator picks an archetype from seller data and then writes the per-seller plan (opening, personalisation, objection playbook, language) so every output is still a persona per seller (FAQ Q1). Evidence grade per archetype is mostly ASSUMED/DOCUMENTED; PS07 supports only the *situations* (rush, re-engage, confusion, Tamil), not the voices.

### Cited Findings
- Sarvam: voice and pace fixed per call; SDK per-call TTS override ignored; language, initial message and variables work per call; fallback is one published agent version per voice profile — PROVEN — [system-design](../../../wiki/projects/vani-hackathon/system-design.md)
- Bulbul v4 catalogue (relevant entries, verbatim descriptors) — PROVEN (our dump) — [catalogue](../../../raw/research/2026-10-07-sarvam-voice-catalogue.json):
  - Aditya – Sales Agent: "confident, low and fast male voice in Hindi… outbound sales"
  - Simran – Hindi Sales Agent: "engaging, low and brisk female voice in Hindi… outbound sales"
  - Ishita – Hindi Numbers Specialist: "warm, slow and expressive female voice in Hindi"
  - Aditya – Conversational Voice: "persuasive, lively and slow male voice in Hindi… outbound sales"
  - Kabir – Conversational Voice: "friendly, low and expressive male voice in Hindi"
  - Aparna – KYC Agent: "professional, low and lively female voice in Hindi"
  - Ritu – Sales Agent: "warm, high and lively female voice in Hindi… outbound sales"
  - Mohit – Conversational Voice: "friendly, highly expressive and light male voice in Hindi"
  - English/Hinglish: Simran – English Sales Agent ("engaging, low and brisk female"), Shalini – Hinglish Support ("warm, low and expressive female, English and Hindi"), Neha – Support ("calm, low and brisk female, English"), Shubh – Expressive Banking ("warm, soft-spoken, expressive male, English and Hindi")
  - **Tamil: only 3 v4 voices, all male and all ad/narration** (Aravind "soft-spoken, highly expressive and deliberate"; Gokul "measured, rough and high"; Vijay "measured, hushed and expressive") — no sales/conversational Tamil voice, no female Tamil voice
- PS07 situations: rush 21% (halves meetings), re-engage type 4.1% vs meeting follow-up 21.7% meeting rate, Tamil markers 46.6% of TN calls, missing-profile sellers convert best (~14–18%) — PROVEN — [persona-data-validation](../../../wiki/projects/vani-hackathon/persona-data-validation.md), [system-design](../../../wiki/projects/vani-hackathon/system-design.md)
- Expressiveness/intelligibility drive Indian TTS preference — DOCUMENTED — [arXiv 2604.21481](https://arxiv.org/html/2604.21481)
- Top sales reps speak slightly slower and lead tempo — DOCUMENTED — [Gong Labs](https://www.gong.io/resources/labs/elements-of-effective-sales-conversations/)

### Inferences
Starting library (ASSUMED unless marked). Pace values are Bulbul `pace` multipliers set in the published version; formality/warmth/brevity/plan style travel per call as variables.

| # | Archetype | Typical seller signal (input, not output) | Voice (primary / alt gender) | Pace | Formality | Warmth | Brevity | Plan style | Basis |
|---|---|---|---|---|---|---|---|---|---|
| A | **Crisp Closer** | high engagement, busy, rush history, meeting-follow-up | Aditya – Sales Agent / Simran – Hindi Sales Agent | 1.05 | medium ("aap", no small talk) | medium-low | very high (≤2 sentences/turn) | value in 1 line → one ask → callback slot if rushed | rush PROVEN prevalent; Gong DOCUMENTED (shorter, not faster); levels ASSUMED |
| B | **Patient Guide** | new/missing-profile, low engagement, confusion history | Ishita – Hindi Numbers Specialist / Aditya – Conversational Voice (both "slow") | 0.9 | low-medium, simple Hindi | high | medium; one idea per turn, check understanding | explain → confirm → small step | confusion signal PROVEN; voice descriptors PROVEN; benefit ASSUMED |
| C | **Respectful Advisor** | higher turnover, manufacturer/exporter, price objections | Kabir – Conversational / Aparna – KYC Agent | 1.0 | high ("ji", full sentences, less slang) | medium | medium | evidence-led: numbers, buyer demand in category, then ask | turnover spread 9.7 pts PROVEN; formality-fit ASSUMED |
| D | **Warm Re-engager** | lapsed / "not interested" history, re-engage type | Ritu – Sales Agent / Mohit – Conversational | 1.0 | low (casual Hinglish) | very high | medium-low | curiosity opener → acknowledge past → low-commitment ask | re-engage 4.1% PROVEN weak segment; style ASSUMED |
| E | **English/Hinglish Professional** (non-Hindi-belt or English-first) | English-dominant sellers, metro/South non-Tamil | Simran – English Sales Agent / Shubh – Expressive Banking | 1.0 | high | medium | high | as C, English-led with Hindi fallback | language fit PROVEN need; voice ASSUMED |
| F | **Tamil Advisor** | TN sellers / Tamil detected | Vijay – Narrator (male only) | 0.95 | medium-high | high | medium | as B/C in Tamil | Tamil gap PROVEN; voice is a narrator, naturalness UNTESTED |

- Sarvam mapping (ASSUMED, follows PROVEN constraint): A–D × primary voice = 4 Hindi versions; E = 1; F = 1 → **6 published versions** for the demo (add alt-gender versions later = up to ~11). Launch chooses `app_version`; per-call variables carry levels, plan and personalisation. Mid-call switches change brevity/tone/language only (voice/pace fixed per call — PROVEN).
- Per-seller output (FAQ Q1): archetype gives the audible base; the generator then sets per-seller opening, personalisation slots (category, city, last enquiry), objection playbook from that seller's past objections, Hinglish ratio, escalation rules, with a reason + confidence per field. Two sellers in the same archetype differ in plan; sellers in different archetypes differ audibly.
- Demo pick for "clearly audible" contrast: A (male, fast-ish, terse) vs B (female, slow, warm) vs F or E (different language) — differs on gender, pace, brevity *and* language at once.
- Evolution (ASSUMED): Day-0 library = designer-led + PS07 situations. Phase 1 (hackathon): simulated sellers (B7) × archetypes, judge + audio metrics to check fit and distinctness. Phase 2 (production): 10% holdout on current VANI; Thompson sampling over archetypes per coarse segment; per-dimension posteriors for formality/warmth/brevity (variables, cheap to test); voice arms only between ≥2 published versions; quarterly library review with keep/tune/drop/split/add rules from Q3.

Devil's advocate:
- **Persona as gimmick:** PS07 shows three personalisation trials failed (PROVEN) — style changes may not move meetings. Counter: claim fit/distinctness and switching, not lift; measure lift only with a holdout.
- **Stereotyping:** "warm = female, authoritative = male" is exactly what the literature warns about (UNESCO; IIS 2025). Our table alternates genders across archetypes and lists an alt-gender voice for each; gender is a tested arm, not a seller-derived rule. Judges may still see "female for confused sellers" as a stereotype — present B with Aditya-Conversational as an equal option.
- **Too few voices per language:** Tamil has 3 male narrator voices only; Gujarati/Punjabi/Bengali have 1–2 conversational voices each (catalogue). For those languages distinctness must come from pace, brevity and plan, which is weaker audibly. Say so explicitly.
- **Judges hearing "minor variations":** within Hindi, pace 0.9 vs 1.05 alone may be barely audible; insist that demo pairs differ on speaker *and* brevity *and* opening style; verify with measured wpm and speaker-embedding distance before the demo.
- **Version sprawl:** every audible change is a new Sarvam published version; 6–11 versions is manageable, a full factorial is not. If Sarvam enables on-start Code Tools (on request), per-call voice override would remove this constraint.
- **Catalogue descriptors are marketing text:** "slow"/"brisk" labels are Sarvam's, not measured; audition and measure before trusting them.
- **Bulbul expressiveness:** the 2026 Indian TTS study found Bulbul v3 less expressive/lively than the top system; v4 not evaluated there, so naturalness in 2+ languages (15%) is a risk to test, not assume.

### Gaps
- No outside or internal evidence on which voice (gender, pitch, pace) converts best for Indian SMB sellers; every voice choice above is ASSUMED pending live/simulated tests.
- Bulbul v4 Tamil narrator voices untested for conversational calls; female Tamil voice absent in v4 catalogue (v3 may have one — not checked).
- Actual audible difference of `pace` 0.9 vs 1.05 on v4 not measured.
