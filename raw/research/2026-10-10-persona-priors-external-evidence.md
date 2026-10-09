# External evidence for persona starting priors, and a check of our method (2026-10-10)

**Sources:**
- the deep-research workflow (5 angles, 19 sources fetched, 82 claims; 25 verified by 3-vote adversarial check; 23 confirmed, 2 refuted). Full JSON: `research_notes/Persona priors external evidence/deep_research_result.json`;
- a last30days scan (2026-09-09 to 2026-10-09). Notes: `research_notes/Persona priors external evidence/last30days.md`.

## A. Voice and persona dimensions (what outside experiments show)
| Dimension | Verified evidence | Confidence | What we take as a prior |
|---|---|---|---|
| **No universal best voice** | Jia et al., SSRN 5202834: 5 field RCTs, 123,946 outbound AI calls. "No universally optimal AI voice". Effects vary by callee gender, price tier, city tier and weekday. Guo et al., MISQ 2025: the effect is stronger in tense calls | HIGH | Voice priors are per segment and **weak**. Structure: a global baseline plus segment deviations |
| Voice gender | Persuasion RCT: no main effect; it matters only together with emotional tone. Debt collection (MISQ 2025): a female voicebot gives **+28.3% odds** of a positive repayment intention; it helps more in tense calls and, in ICIS 2020, with male customers. Gender **matching** is unresolved | MEDIUM | A weak prior: female voice slightly favoured in tense situations (frustrated / irate states). Otherwise flat, and learned by exploration |
| **Opener wording** | Persuasion RCT: **statements beat questions and rhetorical lines**; gentle or firm tone beats flirtatious | MEDIUM | Agrees with our own PS07 result (the enquiry-count statement hook beats the discovery question). Prior: lead with a value statement |
| Interactive vs short | Ma et al., ICIS 2024: ~90K recipients. A one-way recorded call got an 18.43% higher response than an interactive IVR dialogue | LOW | Keep the opening short; don't open with a long discovery exchange |
| Hindi–English code-mixing | Bawa et al., MSR India, CSCW 2020: N=91. Bilinguals prefer bots that code-mix. A "nudge" policy (light mixing, more only if the user mixes) is safe | LOW | Light Hinglish by default; mirror the seller's mixing |
| **AI disclosure** | Luo et al., Marketing Science 2019: field RCT, 6,200+ customers. Undisclosed voice bots sold **as well as proficient humans and 4× better than inexperienced ones**. **Disclosing before the conversation cut purchases by more than 79.7%**; late disclosure hurt less. (last30days: one US inbound report links up-front disclosure to fewer hang-ups. It is correlational and inbound) | MEDIUM | Supports our identity rule: don't volunteer "AI"; sidestep once; "virtual assistant" if pressed; never claim to be human |
| Speaking rate, pitch, formality, warmth, regional accent, social-proof hook | **No verified evidence** | — | **Flat (uninformative) priors.** Only VANI's own exploration can set them |

Transfer limits: no verified study is set in India, B2B or meeting booking. Most are Chinese B2C, several are from before LLMs, and two use stated intention as the outcome.

## B. Is our method right? Mostly yes, with two changes
- **Use a hierarchical prior, not a rule table** (HIGH: Wan et al., AISTATS 2023; Hong & Kveton, ICML 2022). Segment features set each (segment, persona) cell's prior, and each cell can deviate from it (meta / hierarchical Thompson sampling).
  - A fixed segment-to-persona table is brittle: regret can grow **linearly** when the features don't explain the cells.
  - The hierarchy also handles segment explosion, because regret depends less on the number of arms.
  - A meeting is a yes/no outcome, so we use Beta-Bernoulli with partial pooling.
- **Seeded priors only speed up early learning; they never replace exploration** (MEDIUM: NAVER WEBTOON, arXiv 2608.03382, ~595K users per arm; CBLI, arXiv 2406.19317).
  - LLM or outside priors gave no significant overall gain. They helped after a little feedback (+8–10% CTR at 10–49 impressions).
  - One prior turned **harmful (−5.68%)** as data grew.
  - So: keep the priors weak (a small pseudo-count, e.g. κ ≈ 10–40), and keep exploring.
- **Score uplift against a default persona**, not raw bookings (LOW: Amazon causal bandits).
- **Practitioner advice (last30days):**
  - compare options only within the same lead segment;
  - change one thing per test;
  - measure the outcome after the call (meeting held / no repeat contact), not "agreed on the call".

## C. Open issues (not covered by verified evidence; to be designed by us)
1. **Arm attribution when the LLM amends the persona.** Log the final amended persona as the action, with the prior's top-2 and the exploration draw recorded as the propensity. Or limit amendments to a fixed menu of dimension changes with explicit probabilities.
2. **Small traffic:** detecting 1–3 points on a ~12% base needs thousands of calls per arm. During the hackathon the loop can only be **shown working**, not proven.
3. **Fairness with seller gender as a key:** it is used only for the voice choice (team decision 2026-10-10), and its effect is learned from outcomes, not fixed.
4. **Prior strength:** κ must be small enough that a wrong outside prior cannot lock a sparse cell.
