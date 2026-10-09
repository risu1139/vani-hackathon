"""VANI persona code tools for the Sarvam agent (sarvam-conv-ai-sdk 1.1.1). Upload this one file: it replaces all
Python tools on the agent.

OnStart           call start: voice / pace / pitch, starting language and opening line from agent variables.
ReadSellerSignal  read_seller_signal, called by the LLM before every reply. Classifies the seller's latest words
                  (keyword lexicon, romanised + Devanagari + Gujarati + English), applies the per-seller
                  switch_sensitivity, picks the directive variant for persona_style_id and logs one switch_log row
                  {t, turn, utt, lang, script, from, to, cue, directive_id, change, reason, ms, decision_id}.
BookMeeting       book_meeting: sets meeting_fixed = yes and meeting_slot, returns the confirmation text.

Contract: app/contracts/sarvam_vars.contract.json. Every agent variable read or written here must be defined in
the agent. switch_log is never put into message_to_llm (review m5); read it through the analytics API.

Sensitivity (review M4): each cue is strong or weak.
  high    any cue switches on the first turn it is heard;
  normal  a strong cue switches at once; a weak cue needs a second cue of the same signal within 3 turns;
  low     every cue needs a second cue of the same signal within 3 turns.
  opt_out, frustrated and bot_question always switch at once.

Lexicon v1 (2026-10-10), frozen per run. Sources: the 2026-10-09 test set + Jev labels (O2c / W1 relay log,
raw/research/2026-10-09-midcall-switch-tests.md) and frequent PS07 seller n-grams (64,625 seller turns, counts
only). PS07 lessons: "samajh gaya" / "matlab nahi hai" are NOT confusion; "finished recording" is voicemail, not a
bot question; "machine" is often the seller's product; "abhi call mat karo, baad me" is a callback, not an opt-out.
"""
import hashlib
import json
import re
import time
import unicodedata

from pydantic import Field
from sarvam_conv_ai_sdk import (SarvamOnStartTool, SarvamOnStartToolContext, SarvamTool, SarvamToolContext,
                                SarvamToolOutput)
from sarvam_conv_ai_sdk.tool import SarvamToolLanguageName, SpeechSettings, TextToSpeechConfig

LOG_ROWS = 25
LEXICON_VERSION = "lex-v2-20261010"
PACE_RANGE = (0.85, 1.25)
PITCH_RANGE = (-0.3, 0.3)


# ---------------------------------------------------------------- helpers
def _var(context, name):
    try:
        return context.get_agent_variable(name)
    except Exception:
        return None


def _ivar(context, name):
    try:
        return context.get_internal_variable(name)
    except Exception:
        return None


def _setvar(context, name, value):
    try:
        context.set_agent_variable(name, value)
        return True
    except Exception:
        return False


def _num(value, lo, hi):
    try:
        v = float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
    return None if v is None else min(max(v, lo), hi)


def language_enum(name):
    """'GUJARATI' / 'gujarati' / 'Gujarati' -> SarvamToolLanguageName.GUJARATI; unknown -> None."""
    n = (name or "").strip().lower()
    for lang in SarvamToolLanguageName:
        if lang.value.lower() == n:
            return lang
    return None


# ---------------------------------------------------------------- OnStart
class OnStart(SarvamOnStartTool):
    """Apply the seller's VANI persona at call start: voice, pace, pitch, starting language, opening line."""

    async def run(self, context: SarvamOnStartToolContext) -> SarvamOnStartToolContext:
        voice_id = _var(context, "persona_voice_id")
        pace = _num(_var(context, "persona_pace"), *PACE_RANGE)
        pitch = _num(_var(context, "persona_pitch"), *PITCH_RANGE)
        if voice_id or pace is not None or pitch is not None:
            context.text_to_speech_config = TextToSpeechConfig(
                speaker_id=voice_id or None, speech_settings=SpeechSettings(pace=pace, pitch=pitch))
        lang = language_enum(_var(context, "persona_language"))
        if lang is not None:
            context.set_initial_language_name(lang)
            context.set_internal_variable("start_script", LANG_SCRIPT.get(lang.value, ""))
        opening = _var(context, "persona_opening")
        if opening:
            context.set_initial_bot_message(opening)
        return context


# ---------------------------------------------------------------- normalisation
_STRIP = {0x093C, 0x0901, 0x0902, 0x0ABC, 0x0A81, 0x0A82}  # nukta, chandrabindu, anusvara (Devanagari, Gujarati)
_TOKEN_MAP = {"nahin": "nahi", "nhi": "nahi", "nai": "nahi", "nahee": "nahi", "mein": "me", "men": "me",
              "hoon": "hu", "hun": "hu", "hoo": "hu", "bizi": "busy", "bijy": "busy", "biji": "busy",
              "aawaz": "awaz", "awaaz": "awaz", "aavaz": "awaz", "samaj": "samajh", "samjh": "samajh",
              "pareshaan": "pareshan", "dobaara": "dobara"}


def norm(text):
    """Lower case, NFD, drop nukta / anusvara / chandrabindu, punctuation -> space, map common romanised variants."""
    t = unicodedata.normalize("NFD", (text or "").lower())
    t = "".join(ch for ch in t if ord(ch) not in _STRIP)
    t = re.sub("[^\\wऀ-ൿ]+", " ", t)  # keep every Indic block, Devanagari..Malayalam (vowel signs are not \w)
    return " " + " ".join(_TOKEN_MAP.get(w, w) for w in t.split()) + " "


def _is_latin(cue):
    return all(ord(c) < 128 for c in cue)


def _cue_re(cue):
    """Latin cues match whole words (a trailing '*' allows a word prefix); other scripts match as substrings."""
    n = norm(cue.rstrip("*")).strip()
    if _is_latin(n):
        return re.compile(r"(?<![a-z0-9])" + re.escape(n) + ("" if cue.endswith("*") else r"(?![a-z0-9])"))
    return re.compile(re.escape(n))


# ---------------------------------------------------------------- lexicon (mode, strength, cues)
LEXICON = [
    ("opt_out", "strong", (
        "call mat", "phone mat", "call na kare*", "phone na kare*", "number hata*", "number delete", "number block",
        "list se hata*", "dnd", "do not call", "don't call", "dont call", "stop calling", "unsubscribe",
        "कॉल मत", "फोन मत", "call मत", "नंबर हटा", "नंबर डिलीट", "नंबर ब्लॉक", "लिस्ट से हटा",
        "ફોન ન કર", "કોલ ન કર", "કૉલ ન કર", "ફોન મત", "નંબર હટાવ",
        # Marathi, Bengali, Telugu, Tamil, Kannada, Malayalam (v2, 2026-10-10)
        "फोन करू नका", "कॉल करू नका", "ফোন করবেন না", "কল করবেন না", "కాల్ చేయకండి", "ఫోన్ చేయకండి", "నంబర్ తీసేయ",
        "கால் பண்ணாதீங்க", "போன் பண்ணாதீங்க", "ಕಾಲ್ ಮಾಡಬೇಡಿ", "ಫೋನ್ ಮಾಡಬೇಡಿ", "വിളിക്കരുത്", "വിളിക്കണ്ട")),
    ("frustrated", "strong", (
        "kitni baar", "baar baar", "pareshan", "disturb", "faltu", "bakwas", "roz phone", "roz call", "har roz",
        "roz roz", "phone rakh", "warna phone", "dimag mat", "dimag kharab", "irritate*", "band karo", "how many times",
        "कितनी बार", "बार बार", "परेशान", "डिस्टर्ब", "फालतू", "बकवास", "रोज फोन", "रोज कॉल", "हर रोज", "रोज रोज",
        "फोन रख", "वरना फोन", "दिमाग मत", "दिमाग खराब", "बंद करो",
        "કેટલી વાર", "વારંવાર", "હેરાન", "ફાલતુ",
        "किती वेळा", "त्रास देऊ", "কতবার", "বিরক্ত", "ఎన్ని సార్లు", "మళ్ళీ మళ్ళీ", "విసుగు", "చిరాకు",
        "எத்தனை தடவை", "தொந்தரவு", "திரும்ப திரும்ப", "ಎಷ್ಟು ಸಲ", "ತೊಂದರೆ", "ಪದೇ ಪದೇ", "എത്ര തവണ", "ശല്യം")),
    ("bot_question", "strong", (
        "bot ho", "bot hai", "bot se", "robot", "aap machine", "machine ho", "machine se baat", "recorded",
        "recording hai kya", "aap insaan", "insaan ho", "insaan hai", "insaan se baat", "computer bol*",
        "computer se baat", "real person", "are you human", "are you a bot", "ai ho", "ai hai kya", "artificial",
        "बॉट", "रोबोट", "आप मशीन", "मशीन हो", "मशीन से बात", "रिकॉर्डेड", "रिकॉर्डिंग है क्या", "आप इंसान",
        "इंसान हो", "इंसान है", "इंसान से बात", "कंप्यूटर बोल", "कंप्यूटर से बात",
        "રોબોટ", "માણસ છો", "રેકોર્ડ", "bot",
        "माणूस आहात", "রোবট", "মানুষ নাকি", "రోబో", "మనిషేనా", "మనిషా", "కంప్యూటర్ మాట్లాడ", "ரோபோ", "மனுஷனா",
        "மனிதரா", "ರೋಬೋ", "ಮನುಷ್ಯರಾ", "റോബോട്ട്", "മനുഷ്യനാണോ")),
    ("rushed", "strong", (
        "busy", "time nahi", "driving", "drive kar*", "gaadi chala*", "meeting me hu", "meeting me baitha",
        "baad me call", "baad me baat", "baad me phone", "jaldi bolo", "jaldi batao", "call back", "callback",
        "call later", "no time", "baat nahi kar sak*",
        "बिजी", "बिज़ी", "टाइम नही", "समय नही", "ड्राइव", "गाडी चला", "मीटिंग मे हू", "बाद मे कॉल", "बाद मे बात", "बाद मे फोन",
        "जल्दी बोलो", "जल्दी बताओ", "बात नही कर सक",
        "બિઝી", "સમય નથી", "ટાઈમ નથી", "પછી વાત", "પછી ફોન", "પછી કોલ",
        "नंतर बोल", "नंतर फोन", "वेळ नाही", "घाईत आहे", "ব্যস্ত", "বিজি", "পরে কথা", "পরে ফোন", "সময় নেই",
        "బిజీ", "త్వరగా చెప్ప", "తర్వాత మాట్లాడ", "తర్వాత కాల్", "తర్వాత ఫోన్", "టైం లేదు", "సమయం లేదు", "డ్రైవింగ్",
        "பிஸி", "நேரம் இல்லை", "அப்புறம் பேச", "அப்புறம் கால்", "சீக்கிரம் சொல்", "டிரைவிங்",
        "ಬ್ಯುಸಿ", "ಬಿಜಿ", "ಸಮಯ ಇಲ್ಲ", "ಆಮೇಲೆ ಮಾತಾಡ", "ಆಮೇಲೆ ಕಾಲ್", "ಬೇಗ ಹೇಳಿ",
        "ബിസി", "സമയം ഇല്ല", "പിന്നെ വിളിക്ക", "പിന്നെ സംസാരിക്ക",
        "tarvata call", "time ledu", "twaraga cheppandi", "appuram pesu*", "neram illa*", "amele call", "pinne vilikk*",
        "nantar bol*", "pore kotha")),
    ("rushed", "weak", (
        "abhi nahi", "baad me", "thodi der", "kaam me", "bahar hu", "jaldi", "later",
        "अभी नही", "बाद मे", "थोडी देर", "काम मे", "बाहर हू", "जल्दी",
        "હમણા નહી")),
    ("confused", "strong", (
        "samajh nahi", "samajh me nahi", "nahi samajh", "samjha nahi", "samjhi nahi", "kya matlab", "matlab kya",
        "kya kaha", "dobara boli*", "phir se boli*", "awaz nahi", "sunai nahi", "clear nahi",
        "didn't understand", "don't understand", "dont understand", "what do you mean", "pardon", "say again",
        "समझ नही", "समझ मे नही", "नही समझ", "समझा नही", "समझी नही", "क्या मतलब", "मतलब क्या", "क्या कहा",
        "दोबारा बोलि", "फिर से बोलि", "आवाज नही", "सुनाई नही",
        "સમજાયુ નહી", "સમજ ન પડી", "સમજાતુ નથી", "શુ કહ્યુ", "ફરીથી બોલો",
        "समजलं नाही", "समजले नाही", "पुन्हा सांगा", "বুঝলাম না", "বুঝতে পারছি না", "আবার বলুন",
        "అర్థం కాలేదు", "అర్థం కావట్లేదు", "మళ్ళీ చెప్పండి", "ఏమన్నారు", "వినిపించట్లేదు",
        "புரியல", "புரியவில்லை", "மறுபடியும் சொல்", "என்ன சொன்னீங்க", "ಅರ್ಥ ಆಗಲಿಲ್ಲ", "ಮತ್ತೆ ಹೇಳಿ",
        "മനസ്സിലായില്ല", "വീണ്ടും പറയ", "artham kaledu", "puriyala")),
    ("confused", "weak", (
        "kya bol rahe", "kya bola", "phir se bata*", "kaise boli*",
        "क्या बोल रहे", "क्या बोला", "फिर से बता", "कैसे बोलि")),
    ("interested", "strong", (
        "kitna charge", "kitne ka", "charges kya", "kya charge", "charge kitna", "paise kitne", "kitne lagenge",
        "kitna lagega", "price kya", "exact price", "kaise kaam karta", "kaise kaam karega", "kab aayenge",
        "kab aaoge", "kab milenge", "kab mil sakte", "meeting kab", "kitne baje", "mil lete", "aa jaiye",
        "details bhej*", "detail bhej*", "milte hai*", "how much", "what is the price", "how does it work",
        "send details", "when can you come", "let's meet",
        "कितना चार्ज", "कितने का", "चार्ज क्या", "क्या चार्ज", "चार्ज कितना", "पैसे कितने", "कितने लगेगे",
        "कितना लगेगा", "प्राइस क्या", "एग्जैक्ट प्राइस", "कैसे काम करता", "कैसे काम करेगा", "कब आएगे", "कब आओगे",
        "कब मिलेगे", "मीटिंग कब", "कितने बजे", "मिल लेते", "आ जाइए", "आ जाइये", "डिटेल्स भेज", "डिटेल भेज",
        "कैसे मिलेगे", "कैसे आएगे",
        "મીટિંગ ક્યારે", "કેટલા પૈસા", "કેટલો ચાર્જ", "ક્યારે આવશો", "વિગત મોકલ",
        "किती खर्च", "कधी येणार", "मीटिंग कधी", "কত খরচ", "কবে আসবেন", "মিটিং কবে",
        "ఎంత ఖర్చు", "ఎప్పుడు వస్తారు", "మీటింగ్ ఎప్పుడు", "ఎలా పని చేస్తుంది", "వివరాలు పంప",
        "எப்போ வருவீங்க", "மீட்டிங் எப்போ", "எப்படி வேலை செய்யும்", "ಯಾವಾಗ ಬರ್ತೀರಾ", "ಮೀಟಿಂಗ್ ಯಾವಾಗ",
        "എപ്പോൾ വരും", "മീറ്റിംഗ് എപ്പോൾ")),
    ("interested", "weak", (
        "price batao", "kaise hoga", "batao kaise", "aa jao", "kya fayda",
        "प्राइस बताओ", "कैसे होगा", "बताइए कैसे", "आ जाओ", "क्या फायदा",
        "કેવી રીતે")),
]
_COMPILED = [(mode, strength, cue, _cue_re(cue)) for mode, strength, cues in LEXICON for cue in cues]
PRIORITY = ["opt_out", "frustrated", "bot_question", "rushed", "confused", "interested"]
ALWAYS_NOW = {"opt_out", "frustrated", "bot_question"}
_LATER = re.compile(r"(?<![a-z])(baad|kal|shaam|later|tomorrow|evening|tarvata|appuram|amele|pinne|nantar)(?![a-z])|"
                    r"बाद|कल|शाम|પછી|કાલે|नंतर|পরে|తర్వాత|రేపు|அப்புறம்|நாளை|ಆಮೇಲೆ|ನಾಳೆ|പിന്നെ|നാളെ")
_NOT_WANTED = re.compile(r"(?<![a-z])(nahi chahiye|interest nahi|not interested|zarurat nahi)(?![a-z])|नही चाहिए|"
                         r"इंटरेस्ट नही|जरूरत नही|નથી જોઈએ")


def find_cues(text):
    """All lexicon hits in an utterance: list of (mode, strength, cue)."""
    t = norm(text)
    return [(mode, strength, cue) for mode, strength, cue, rx in _COMPILED if rx.search(t)]


def classify(text):
    """Strongest signal in one utterance -> (mode, strength, cue, note). mode 'neutral' when nothing matched."""
    t = norm(text)
    hits = find_cues(text)
    note = ""
    if any(m == "opt_out" for m, _, _ in hits) and _LATER.search(t):
        # "abhi call mat karo, baad me karna" = a callback request, not an opt-out (PS07 lesson)
        hits = [h for h in hits if h[0] != "opt_out"] + [("rushed", "strong", "call mat + later")]
        note = "opt-out phrase with a later time = callback"
    if _NOT_WANTED.search(t):
        hits = [h for h in hits if h[0] != "interested"]
    for strength in ("strong", "weak"):  # a strong cue of a lower-priority signal beats a weak cue
        for mode in PRIORITY:
            mh = [h for h in hits if h[0] == mode and h[1] == strength]
            if mh:
                return mode, strength, mh[0][2], note
    return "neutral", "", "", note


# ---------------------------------------------------------------- language by script
SCRIPTS = {"deva": (0x0900, 0x097F), "beng": (0x0980, 0x09FF), "guru": (0x0A00, 0x0A7F), "gujr": (0x0A80, 0x0AFF),
           "orya": (0x0B00, 0x0B7F), "taml": (0x0B80, 0x0BFF), "telu": (0x0C00, 0x0C7F), "knda": (0x0C80, 0x0CFF),
           "mlym": (0x0D00, 0x0D7F)}
SCRIPT_LANG = {"deva": "Hindi", "beng": "Bengali", "guru": "Punjabi", "gujr": "Gujarati", "orya": "Odia",
               "taml": "Tamil", "telu": "Telugu", "knda": "Kannada", "mlym": "Malayalam", "latn": "English"}
LANG_SCRIPT = {"Hindi": "deva", "Marathi": "deva", "Konkani": "deva", "Bengali": "beng", "Assamese": "beng",
               "Punjabi": "guru", "Gujarati": "gujr", "Odia": "orya", "Tamil": "taml", "Telugu": "telu",
               "Kannada": "knda", "Malayalam": "mlym", "English": "latn"}


# English function words: a Latin-script turn is English only if it uses them (romanised Telugu / Hindi is not English)
_EN_FUNC = set("the a an is are am was i you we it this that what why how when where can could will would do does did "
               "not please to of in on for with my your me and or but be have has there here now just so if".split())


def script_of(text):
    """Dominant script of an utterance. Latin counts as English only with >= 3 latin words and >= 70% latin letters
    (ASR writes code-mixed English words in Latin inside Hindi turns)."""
    counts = dict.fromkeys(list(SCRIPTS) + ["latn"], 0)
    for ch in text or "":
        o = ord(ch)
        if ch.isascii():
            if ch.isalpha():
                counts["latn"] += 1
            continue
        for s, (lo, hi) in SCRIPTS.items():
            if lo <= o <= hi:
                counts[s] += 1
                break
    total = sum(counts.values())
    if not total:
        return "none"
    best = max(counts, key=counts.get)
    if best == "latn":
        words = re.findall(r"[a-z']+", (text or "").lower())
        english = sum(w in _EN_FUNC for w in words)
        if len(re.findall(r"[A-Za-z]{2,}", text or "")) < 3 or counts["latn"] < 0.7 * total or english < max(2, 0.25 * len(words)):
            others = {k: v for k, v in counts.items() if k != "latn" and v}
            return max(others, key=others.get) if others else "none"
    return best


# ---------------------------------------------------------------- directives (per mode x persona style)
STYLE_WPT = {"P0": 20, "P1": 18, "P2": 15, "P3": 14, "P4": 10, "P5": 16, "P6": 20, "COMPOSED": 18}
MODE_CAP = {"neutral": 20, "rushed": 12, "frustrated": 18, "confused": 20, "interested": 20, "bot_question": 20,
            "opt_out": 15, "language_switch": 20}
_D = {  # mode -> style -> (word cap, text); "*" = any style without its own variant. {cap} is filled in.
    "rushed": {
        "*": (12, "Seller is busy. ONE short sentence, max {cap} words: the value in a few words, then ask when to call back."),
        "P1": (12, "Seller is busy. ONE sentence, max {cap} words: one fact from verified facts, then ask when to call back."),
        "P2": (12, "Seller is busy. ONE short friendly sentence in their language, max {cap} words; ask when you may call back."),
        "P3": (10, "Seller is busy. Do not explain anything. ONE sentence, max {cap} words: ask when you may call back."),
        "P4": (10, "Seller is busy. ONE sentence, max {cap} words: offer a short callback and ask the time."),
        "P5": (12, "Seller is busy. ONE polite sentence, max {cap} words; respect their time, ask when to call back."),
        "P6": (12, "Seller is busy. ONE courteous sentence, max {cap} words; ask for a convenient callback time."),
    },
    "frustrated": {
        "*": (18, "Seller is irritated. Apologise in a few words, do not repeat the pitch, ask one yes/no question. Max {cap} words."),
        "P2": (15, "Seller is irritated. Say sorry warmly in a few words, no pitch, ask one simple yes/no question. Max {cap} words."),
        "P3": (15, "Seller is irritated. Say sorry calmly, no pitch, one simple yes/no question. Max {cap} words."),
        "P4": (12, "Seller is irritated. Short apology, no pitch, one yes/no question. Max {cap} words."),
        "P5": (18, "Seller is irritated. Acknowledge the problem once, sincerely; do not argue or pitch; one yes/no question about fixing it in a meeting. Max {cap} words."),
        "P6": (16, "Seller is irritated. Apologise courteously, no pitch, one yes/no question. Max {cap} words."),
    },
    "confused": {
        "*": (20, "Seller is confused. Re-explain ONE idea in very simple words, as short phrases of 3-4 words separated by commas, then check understanding. Max {cap} words."),
        "P2": (16, "Seller is confused. In their own language, simple local words, short comma phrases, one idea, then check understanding. Max {cap} words."),
        "P3": (16, "Seller is confused. Slower: short comma phrases of 3-4 words, one idea, then ask if it is clear. Max {cap} words."),
        "P4": (14, "Seller is confused. One idea, short comma phrases, then check understanding. Max {cap} words."),
        "P6": (20, "Seller is confused. Re-explain one idea plainly, short phrases separated by commas, no jargon, then check understanding. Max {cap} words."),
    },
    "interested": {
        "*": (20, "Seller is interested. Answer in one short line using only verified facts, then ask a day and time for our IndiaMART executive's meeting. Do not pitch again. Max {cap} words."),
        "P1": (18, "Seller is interested. One line with one verified fact, then ask a day and time for the meeting. Do not pitch again. Max {cap} words."),
        "P4": (12, "Seller is interested. Skip details; ask a day and time for the meeting. Max {cap} words."),
    },
    "bot_question": {
        "*": (20, "Seller asked if you are a bot or a person. Do not say AI or bot, never claim to be human. Say you are calling from IndiaMART about their profile, then return to the call plan. Max {cap} words."),
        "P4": (14, "Seller asked if you are a bot. Never say AI or bot, never claim to be human: you are calling from IndiaMART about their profile, then the plan. Max {cap} words."),
    },
    "bot_question_pressed": {
        "*": (20, "Seller asked again if you are a bot. Say you are IndiaMART's virtual assistant (never AI, never human) and offer a callback from an IndiaMART executive. Max {cap} words."),
    },
    "opt_out": {
        "*": (15, "Seller does not want calls. Apologise, confirm they will not be called again, thank them, end the call. No pitch. Max {cap} words."),
    },
    "language_switch": {
        "*": (20, "Seller switched to {lang}. Reply in {lang} from now on, same persona and rules. Max {cap} words."),
    },
    "neutral": {
        "*": (20, "Continue the call plan. Max {cap} words."),
    },
}


def directive(mode, style_id, lang=""):
    """(directive_id, word cap, text) for a mode and persona style. Neutral uses the persona's words per turn."""
    style = (style_id or "").strip().upper() or "COMPOSED"
    variants = _D[mode]
    key = style if style in variants else "*"
    cap, text = variants[key]
    if mode == "neutral":
        cap = min(STYLE_WPT.get(style, 18), MODE_CAP["neutral"])
    return f"{mode}.{key if key != '*' else 'base'}.v1", cap, text.format(cap=cap, lang=lang or "the seller's language")


_CHANGE = {"neutral": "default persona style", "rushed": "brevity + callback offer", "frustrated": "apology, pitch stopped",
           "confused": "simplify: short comma phrases + check", "interested": "move to meeting day/time",
           "bot_question": "identity sidestep", "bot_question_pressed": "virtual-assistant line + human callback",
           "opt_out": "apology + end call", "language_switch": "reply language"}

OPT_OUT_LINE = {
    "Hindi": "माफ़ कीजिए, अब आपको हमारी तरफ से कॉल नहीं आएगा। धन्यवाद।",
    "Gujarati": "માફ કરશો, હવે તમને અમારી તરફથી કૉલ નહીં આવે. આભાર.",
    "English": "Sorry for the trouble. You will not get calls from us again. Thank you.",
    "Marathi": "माफ करा, आता तुम्हाला आमच्याकडून कॉल येणार नाही. धन्यवाद.",
    "Tamil": "மன்னிக்கவும், இனி உங்களுக்கு எங்களிடமிருந்து அழைப்பு வராது. நன்றி.",
}


def _sensitivity(raw, mode):
    try:
        d = json.loads(raw) if raw else {}
        v = str(d.get(mode, "normal")).lower() if isinstance(d, dict) else "normal"
    except Exception:
        v = "normal"
    return v if v in ("high", "normal", "low") else "normal"


def decide(mode, strength, sensitivity, recent_modes):
    """Switch now? recent_modes = cue modes heard in the previous 2 turns. Returns (switch, reason)."""
    if mode == "neutral":
        return True, "no cue"
    if mode in ALWAYS_NOW:
        return True, f"{mode} always switches at once"
    repeat = mode in recent_modes
    if sensitivity == "high":
        return True, "sensitivity high: first cue switches"
    if sensitivity == "normal" and strength == "strong":
        return True, "sensitivity normal: strong cue"
    if repeat:
        return True, f"sensitivity {sensitivity}: second {mode} cue within 3 turns"
    return False, f"sensitivity {sensitivity}: {strength} cue, waiting for a second cue within 3 turns"


def _append_log(context, row):
    try:
        log = json.loads(_var(context, "switch_log") or "[]")
        if not isinstance(log, list):
            log = []
    except Exception:
        log = []
    log.append(row)
    _setvar(context, "switch_log", json.dumps(log[-LOG_ROWS:], ensure_ascii=False))


def _jlist(raw):
    try:
        v = json.loads(raw) if raw else []
        return v if isinstance(v, list) else []
    except Exception:
        return []


class ReadSellerSignal(SarvamTool):
    """Reads the seller's latest words and returns how to adapt your next reply (seller mode and a short directive). Call this tool after EVERY seller turn, before you reply, passing the seller's last utterance exactly as spoken. Also call it when the seller switches language."""

    seller_utterance: str = Field(description="The seller's most recent utterance, copied word for word as spoken.")
    language: str = Field(default="", description="Language the seller just spoke in: hinglish, hindi, english, gujarati, tamil, other.")

    async def run(self, context: SarvamToolContext) -> SarvamToolOutput:
        t0 = time.perf_counter()
        utt = self.seller_utterance or ""
        prev = _var(context, "seller_mode") or "neutral"
        style = _var(context, "persona_style_id") or "COMPOSED"
        turn = int(_ivar(context, "turn") or 0) + 1
        h = hashlib.sha256(norm(utt).strip().encode("utf-8")).hexdigest()[:12]
        script = script_of(utt)
        row = {"t": round(time.time(), 2), "turn": turn, "utt": utt[:80], "lang": self.language, "script": script,
               "from": prev, "decision_id": _var(context, "decision_id") or "", "lex": LEXICON_VERSION}

        if h == _ivar(context, "last_utt_hash"):  # same utterance twice in a row: no change, logged as dup
            row.update({"turn": turn - 1, "to": prev, "cue": "", "directive_id": "", "change": "none", "dup": True,
                        "reason": "duplicate call for the same utterance", "ms": round((time.perf_counter() - t0) * 1000, 2)})
            _append_log(context, row)
            return SarvamToolOutput(message_to_llm=f"No change. Seller mode: {prev} | Directive: {_var(context, 'persona_directive')}",
                                    context=context)
        context.set_internal_variable("last_utt_hash", h)
        context.set_internal_variable("turn", turn)

        mode, strength, cue, note = classify(utt)
        # language switch: dominant script differs from the last seller turn (or from the persona's start language)
        last_script = _ivar(context, "last_script") or _ivar(context, "start_script") or ""
        if not last_script:
            start = language_enum(_var(context, "persona_language"))
            last_script = LANG_SCRIPT.get(start.value, "") if start is not None else ""
        lang_switch = script not in ("none", "") and last_script and script != last_script
        if script not in ("none", ""):
            context.set_internal_variable("last_script", script)
        new_lang = SCRIPT_LANG.get(script, "") if lang_switch else ""
        lang_set = ""
        if lang_switch:
            target = language_enum(new_lang)
            try:
                if target is not None and context.get_current_language() != target:
                    context.change_language(target)
                    lang_set = new_lang
            except Exception:
                lang_set = "not allowed"

        sens = _sensitivity(_var(context, "switch_sensitivity"), mode) if mode != "neutral" else ""
        hist = _jlist(_ivar(context, "cue_hist"))
        recent = [m for turn_modes in hist[-2:] for m in turn_modes]
        switch, reason = decide(mode, strength, sens, recent)
        context.set_internal_variable("cue_hist", json.dumps((hist + [[mode] if mode != "neutral" else []])[-3:]))
        if note:
            reason = f"{note}; {reason}"

        if mode != "neutral" and not switch:
            to = prev  # cue heard but under the seller's threshold: keep the current mode
        elif mode == "neutral" and lang_switch:
            to = "language_switch"
        else:
            to = mode
        dmode = to
        if to == "bot_question":
            n = int(_ivar(context, "bot_q_count") or 0) + 1
            context.set_internal_variable("bot_q_count", n)
            if n >= 2:
                dmode = "bot_question_pressed"
        did, cap, text = directive(dmode, style, new_lang)
        if lang_switch and to != "language_switch":
            text += f" Reply in {new_lang}."
        if lang_switch:
            reason += f"; script {last_script}->{script}" + (f" (set {lang_set})" if lang_set else "")

        _setvar(context, "seller_mode", to)
        _setvar(context, "persona_directive", text)
        row.update({"to": to, "cue": cue + (f" [{strength}]" if cue else ""), "directive_id": did,
                    "change": _CHANGE.get(dmode, "") + (f" + reply in {new_lang}" if lang_switch and to != "language_switch" else "")
                    if (to != prev or lang_switch) else "none (same mode)",
                    "reason": reason, "sens": sens, "dup": False, "ms": round((time.perf_counter() - t0) * 1000, 2)})
        _append_log(context, row)

        if to == "opt_out":
            context.set_end_conversation()
            try:
                cur = context.get_current_language().value
            except Exception:
                cur = "Hindi"
            return SarvamToolOutput(message_to_user=OPT_OUT_LINE.get(cur, OPT_OUT_LINE["Hindi"]),
                                    message_to_llm=f"Seller mode: opt_out | {text}", context=context)
        return SarvamToolOutput(message_to_llm=f"Seller mode: {to} | Directive for your next reply: {text}", context=context)


# ---------------------------------------------------------------- BookMeeting
class BookMeeting(SarvamTool):
    """Books the meeting with our IndiaMART executive. Call it ONLY after the seller has clearly agreed to a meeting AND a day/time. Pass the slot exactly as agreed, in natural language (e.g. 'kal shaam 5 baje', 'Monday 11 am')."""

    slot: str = Field(description="The day and time the seller agreed to, in natural language, as the seller said it.")
    place: str = Field(default="", description="Where, if the seller said (shop, office, phone call); else empty.")

    async def run(self, context: SarvamToolContext) -> SarvamToolOutput:
        slot = (self.slot or "").strip()
        if len(slot) < 2:
            return SarvamToolOutput(message_to_llm="Not booked: no day and time yet. Ask the seller for a day and time first.",
                                    context=context)
        value = slot[:120] + (f" @ {self.place.strip()[:60]}" if self.place.strip() else "")
        ok = _setvar(context, "meeting_fixed", "yes") & _setvar(context, "meeting_slot", value)
        _append_log(context, {"t": round(time.time(), 2), "turn": int(_ivar(context, "turn") or 0), "utt": "",
                              "from": _var(context, "seller_mode") or "neutral", "to": _var(context, "seller_mode") or "neutral",
                              "cue": "book_meeting", "directive_id": "book_meeting.v1",
                              "change": f"meeting_fixed=yes, slot={value[:60]}", "reason": "seller agreed a slot",
                              "decision_id": _var(context, "decision_id") or "", "ms": 0})
        if not ok:
            return SarvamToolOutput(message_to_llm="Booking could not be saved. Do not claim it is booked; say our IndiaMART executive will call to confirm the time, then thank the seller and close.",
                                    context=context)
        return SarvamToolOutput(
            message_to_llm=(f"Booked: {value}. Confirm this slot once in the seller's language, say our IndiaMART "
                            "executive will meet them then, thank them and close the call. Max 20 words."),
            context=context)
