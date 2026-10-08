> This page is for Model APIs.

> For clean Markdown of any page, append `.md` to the page URL.
> For a complete documentation index, see https://docs.sarvam.ai/llms.txt.
> For full documentation content in one file, see https://docs.sarvam.ai/llms-full.txt.
> For AI client integration (Claude Code, Cursor, etc.), connect to the MCP server at https://docs.sarvam.ai/_mcp/server.

# Voices

> Listen to every Sarvam AI text-to-speech voice before you choose. Audio previews for all Bulbul v3 speakers, including multilingual samples.

Listen to every voice before you pick one for your product. Each sample below reads the same expressive line, **"वाह, यह तो कमाल है! Sarvam AI के साथ अपनी भाषा में बात करना अब बहुत आसान हो गया है।"** ("Wow, this is amazing! Talking in your own language with Sarvam AI has become so easy now."), so you can compare voices directly and hear how each one handles natural emotion and prosody. Use the `speaker` parameter to select any of these in your API calls; see [How to change the speaker voice](/api/api-guides-tutorials/text-to-speech/how-to/change-the-speaker-voice) for code samples.

> **Note**
>
> Want to test your own text? Head to [dashboard.sarvam.ai](https://dashboard.sarvam.ai/text-to-speech) to generate live previews with custom input.

> **Tip**
>
> Not sure which voice to pick? [Best Practices: Speaker Selection](/api/api-guides-tutorials/text-to-speech/best-practices) ranks every voice by measured pronunciation accuracy (CER) and recommends the best speaker per language.

> **Tip**
>
> Need a voice that isn't in this list? The [Voice Cloning API](/api/api-guides-tutorials/voice-cloning/overview) generates speech in a cloned voice from a short reference clip, or in a saved voice via `voice_id` — usable from the same SDK alongside these speakers.

---

## Bulbul v3 Male Voices

> **Note**
>
> Speaker names are case-sensitive and must be lowercase (e.g., `shubh`, not `Shubh`).

> **Warning**
>
> **varun** produces a deep, dramatic tone suited to suspense or villain characters. It is not recommended as a neutral default and should be reserved for thriller, drama, or suspense use cases.

## Bulbul v3 Female Voices

All voices are optimized for natural conversations and high-quality audio output.

[Learn more about Bulbul v3 →](/api/getting-started/models/bulbul)

---

## Hear Voices Across Languages

Bulbul v3 supports 11 languages, and voice quality varies by language. Below, two of our top-rated speakers, **shubh** (male) and **ishita** (female), read the same localized line in each supported language, translated with [Sarvam Translate](/api/api-guides-tutorials/text-processing/translation).

English · en-IN

shubh (male)

ishita (female)

Hindi · hi-IN

shubh (male)

ishita (female)

Bengali · bn-IN

shubh (male)

ishita (female)

Tamil · ta-IN

shubh (male)

ishita (female)

Telugu · te-IN

shubh (male)

ishita (female)

Kannada · kn-IN

shubh (male)

ishita (female)

Malayalam · ml-IN

shubh (male)

ishita (female)

Marathi · mr-IN

shubh (male)

ishita (female)

Gujarati · gu-IN

shubh (male)

ishita (female)

Punjabi · pa-IN

shubh (male)

ishita (female)

Odia · od-IN

shubh (male)

ishita (female)

> **Tip**
>
> shubh and ishita are a safe starting point for any language, but they are not always the top performer, so check the [per-language recommendations](/api/api-guides-tutorials/text-to-speech/best-practices) for the best male/female pick in your target language.

---

## Generate Your Own Sample

#### Python

```python
from sarvamai import SarvamAI
from sarvamai.play import save

client = SarvamAI(api_subscription_key="YOUR_SARVAM_API_KEY")

audio = client.text_to_speech.convert(
    text="वाह, यह तो कमाल है! Sarvam AI के साथ अपनी भाषा में बात करना अब बहुत आसान हो गया है।",
    model="bulbul:v3",
    language_code="hi-IN",
    speaker="ishita"
)
save(audio, "preview.wav")
```

#### cURL

```bash
curl -X POST https://api.sarvam.ai/text-to-speech \
  -H "api-subscription-key: <YOUR_SARVAM_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "वाह, यह तो कमाल है! Sarvam AI के साथ अपनी भाषा में बात करना अब बहुत आसान हो गया है।",
    "language_code": "hi-IN",
    "speaker": "ishita",
    "model": "bulbul:v3"
  }'
```

## Next Steps

#### [Change the Speaker Voice](/api/api-guides-tutorials/text-to-speech/how-to/change-the-speaker-voice)

Learn how to set the `speaker` parameter in your API calls.

#### [Best Practices](/api/api-guides-tutorials/text-to-speech/best-practices)

See CER-ranked quality tiers and per-language speaker recommendations.