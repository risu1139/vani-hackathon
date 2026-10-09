# Team decision: starting voice and language priors (2026-10-10)

Source: the user, in the planning session on 2026-10-10, after the external-evidence research (`raw/research/2026-10-10-persona-priors-external-evidence.md`).

## Verbatim
> this was in us saying ai won't work in india it is unchanged starting points matter the most that is good. the best voice depends on the callee's gender, price tier, city tier, weekday and how tense the call is record this and we will write in skill as well this becomes one of the role we do not have data so we will favour female voice. Slight lean to a female voice for frustrated/irate sellers and also in hindi belt rular aread or any rural area do we have infomation for this. Keep the opening short and interactive. idealy in our match will be for regional language unless high value

## Decisions
1. **AI disclosure is unchanged.** The study that links up-front disclosure to fewer hang-ups is US data, and it does not apply in India. VANI never volunteers "AI" (see `2026-10-10-team-decision-vani-identity-line.md`).
2. **Starting points matter most.** With no data of our own, the starting priors decide the early calls.
3. **Guiding principle for the skill:** the best voice depends on the callee's gender, price tier, city tier, weekday, and how tense the call is (field evidence: SSRN 5202834, MISQ 2025). The persona agent must weigh these, not use one global voice.
4. **Default voice: female**, because we have no data. Lean further to female for:
   - frustrated or irate sellers;
   - Hindi-belt rural areas, and any rural area.
5. **Opening: short and interactive.**
6. **Language: match the seller's regional language**, unless the seller is high value. For high-value sellers the agent decides; for example Hinglish or English for sophistication.

## Data for "rural" (checked in the same session)
pg-imblr `gl_city.gl_city_classification`:
- 1 = 11 metros;
- 2 = 49 tier-2 cities;
- 3 = 7,700 smaller towns;
- empty = 21,547 places (mostly villages and very small towns).

Proxy: classification 3 or empty = small town / rural. Hindi belt = the state is in UP, Bihar, MP, Rajasthan, Haryana, Jharkhand, Chhattisgarh, Uttarakhand, Himachal Pradesh or Delhi. The builder must add the seller's city classification to the context. This is a proxy, not a census rural flag.

## Later in the same session (user, who identified as Rishav)
- Scoreboard outcome: "meeting fixed" now; "meeting held" is added later.
- Rishav approves new versions of the persona library and the Sarvam template.
- The "AI Roleplay" recordings have real salespeople on the IndiaMART side (not AI). Use them to build the CSD pitch reference. NSD follows the enrichment-meeting principles; test that the agent follows them.
