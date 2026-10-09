# VANI on Sarvam: repeatable runbook

How a seller's persona becomes a Sarvam call, and how to test it. Every step runs from a file in this repo.
Rule: build and change things through files and the Python SDK; the console UI is for guidance only.

## 1. Persona → variables (laptop, no Sarvam credits)

```
python app/persona/export_for_agent.py --glid <GLID>                       # pseudonymised folder + name map
python .claude/skills/vani-persona/run_persona.py \
       --folder data/agent_export/<pseudo> --names data/agent_export_maps/<pseudo>.json --decision-id <id>
```

Output in `data/runs/<id>/`:

| File | What |
|---|---|
| `04_persona.json` | the persona (Opus 5.5), validated |
| `05_sarvam_vars.json` | the agent variables for this call (contract: `app/contracts/sarvam_vars.contract.json`) |
| `06_sarvam_prompt.md` | the full prompt this seller's call will use (skeleton + variables filled); read this to review |

To recompile after a code change, without running the agent again:
`python .claude/skills/vani-persona/scripts/compile_vars.py --run data/runs/<id> --names data/agent_export_maps/<pseudo>.json`

## 2. How the persona reaches Sarvam

- **One fixed prompt in the agent**: `app/sarvam/vani_prompt.md`. Each section is filled by a variable. The persona and hook drive the text; the template does not change per seller.
  - `@prompt_persona`, `@prompt_environment`, `@prompt_objective` (division + **hook**), `@prompt_style`, `@prompt_facts`, `@prompt_phases` (call plan + objections), `@prompt_guardrails`.
  - In the stored config, the prompt is plain text in `llm_config.agent_config.states.start.instructions` with `{{variable}}` placeholders. The console shows it as Tiptap `@mentions`.
- **Voice, pace, pitch, language, opening**: `OnStart` in `app/sarvam/vani_tools.py` reads `persona_voice_id`, `persona_pace`, `persona_pitch`, `persona_language` and `persona_opening`.
- **Mid-call switching**: `read_seller_signal` (keyword lexicon `lex-v2`) returns a directive on the same turn. Nothing re-fills the prompt mid-call. Voice and pace stay fixed; brevity comes from the directive.
- Sarvam fills variables in one pass, so `compile_vars` resolves any `@var` inside a section before it is sent.

## 3. Agent setup (once per template change)

| Item | Source file | Where it goes |
|---|---|---|
| Prompt skeleton | `app/sarvam/vani_prompt.md` (`@x` becomes `{{x}}`) | `states.start.instructions` |
| Variables | `app/contracts/sarvam_vars.contract.json` (all keys) | `agent_config.agent_variables` (each must be defined, or Sarvam drops it) |
| Tools | `app/sarvam/vani_tools.py` | console tool upload (passes Sarvam's code audit) |
| Settings | `app/sarvam/agent.json` (`settings`) | Eagerness = Patient; language switching on; per-language voices off |

Status (2026-10-10): the clone `VANI-person-b8c173ff-b272` still has the 11-variable prompt and the `lex-v1` tools. It is a **draft** (not published).

**Why not the SDK:** `sarvam-conv-ai-sdk` (1.1.1, the latest) is runtime only: conversations, variables, tool classes. It has no create, update, upload or publish calls.

**Authoring API** (what the console calls). Base: `https://apps.sarvam.ai/api/app-authoring/orgs/{org}/workspaces/{ws}/apps`. Auth: the console login (Bearer), not the API key (the API key gets 401).

| Action | Call |
|---|---|
| Read config | `GET /{app}?app_version=N&version_filter=specific&legacy=true` |
| Validate | `POST /validate` body `{app, tools: []}` → `{"detail": []}` when valid |
| Save draft | `PUT /{app}` body `{app: <config without metadata keys>, app_name}` |
| Upload tools | `PUT /{app}/tools?forceUpload=false` (multipart form) |
| Publish version | `POST /{app}/commit` body `{app_version_description}` |
| Versions | `GET /{app}/versions?legacy=true` |

Metadata keys removed before saving: `org_id, workspace_id, app_id, app_name, app_version, app_version_description, created_by, updated_by, created_at, updated_at, status, channel_provider, is_deployed, is_single_prompt_mode`.

Payload for the section template (built from files): `data/sarvam_backups/clone_update_payload.json`. It sets `states.start.instructions`, adds the 7 `prompt_*` variables and drops the 5 old ones. Validation of this payload passed (2026-10-10). Backup of the config before the change: `data/sarvam_backups/VANI-person-b8c173ff-b272_v1_20261010_before_lexv2.json`.

## 4. Test (cheap, text only)

Two routes:

| Route | Needs | Works on a draft? | Command |
|---|---|---|---|
| A. SDK text session | `SARVAM_AGENTS_API_KEY` (in `.env`) | **no**: the runtime returns 404 until the version is published | `python app/spike/persona_text_smoke.py --run data/runs/<id>` |
| B. Console playground endpoint | the console login (browser) | yes | in the logged-in console page: POST `{runtime}/channels/text-chat/orgs/{org}/workspaces/{ws}/apps/{app}/text-chat?app_version=N` with `{text, start_interaction, interaction_id, override_agent_variable_values, initial_language_name, debug: true}` |

Route A is the repeatable one: publish the clone version once, then the smoke runs from files with the API key.
Route B needs the console token, which must stay in the browser (saving it to a file is blocked as credential handling).

The smoke test checks:

1. The variables render: the opening, the hook and the objection answers come from the persona.
2. `read_seller_signal` runs on every turn.
3. A "busy" line switches to rushed on the same turn.
4. A bot question gets the sidestep.

Keep it to 2 sessions of at most 4 turns each.

## 5. After the call

`python app/sarvam/collect_call.py --interaction-id <id>` gives `06_call.json` + `07_outcome.json` (analytics API, `X-API-Key`).

## Log

| Date | What | Result |
|---|---|---|
| 2026-10-10 | Playground smoke, Telugu CSD seller (route B, legacy 11-variable prompt with the new sections inside) | Long variables render (~12K chars); hook word for word; objection from the playbook; bot sidestep OK; tool on 6/6 turns; ~2.5 s/turn. **Fails:** Telugu "busy" was not rushed; romanised Telugu read as English. Fixed in `lex-v2` (regional cues for mr/bn/te/ta/kn/ml; Latin = English only with English function words). The fix is not uploaded to the clone yet. |
