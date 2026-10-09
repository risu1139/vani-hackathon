"""Jev on native-script seller turns (as live Sarvam ASR delivers them) vs romanized text.

Conditions:
  A  romanized text  + current (romanized-cue) questions   -> baseline from the 2026-10-07 spike
  B  native script   + current questions
  C  native script   + questions whose criteria add native-script cue examples
Hand-written test sentences; not customer data.
Usage: python app/spike/jev_devanagari.py
"""
import copy
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from jev_spike import CASES, QUESTIONS, ROOT, decide as _decide_base  # noqa: F401  (decide uses QUESTIONS global)
import jev_spike

# Native-script versions of jev_spike.CASES (same order, same labels), written as ASR would output them.
NATIVE = [
    "अभी बिज़ी हूँ यार, जल्दी बोलो क्या है",
    "मैं ड्राइविंग कर रहा हूँ, बाद में कॉल करो",
    "टाइम नहीं है अभी, शॉर्ट में बताओ",
    "मीटिंग में हूँ, शाम को बात करते हैं",
    "சீக்கிரம் சொல்லுங்க, நான் பிஸி",
    "હું અત્યારે બિઝી છું, પછી વાત કરું",
    "कितनी बार कॉल करोगे, परेशान कर दिया है",
    "फालतू कॉल मत करो भाई, दिमाग मत खाओ",
    "ये तीसरी बार कॉल आ रहा है आज, बंद करो ये सब",
    "समझ नहीं आया, क्या मतलब मीटिंग?",
    "क्या बोला आपने? किस चीज़ का कॉल है ये?",
    "என்ன சொல்றீங்க, புரியல",
    "आप बॉट हो क्या? रिकॉर्डेड कॉल है?",
    "किसी इंसान से बात कराओ, मशीन से नहीं",
    "Are you a robot or a real person?",
    "अच्छा, कितना चार्ज है इसका?",
    "ठीक है, कल ग्यारह बजे आ जाइए ऑफिस",
    "डिटेल्स व्हाट्सएप पे भेज दो, देखता हूँ",
    "તમે કેટલા પૈસા લેશો? મને ડિટેલ્સ મોકલો",
    "हाँ बोलिए",
    "हाँ जी, मैं ही बोल रहा हूँ",
    "आपका नाम क्या है और कौन सी कंपनी से हो?",
    "नहीं चाहिए, इंटरेस्ट नहीं है, थैंक यू",
    "ऑलरेडी इंडियामार्ट वाले सर से बात हो गई है",
    "ओके ओके",
    "Yes tell me, what is this about?",
    "இல்ல, வேண்டாம்",
    "મને કંઈ સમજાયું નહીં, શું કામ છે?",
    "अभी नहीं, महीने बाद कॉल करना",
    "भाई पहले भी बोला था मुझे नहीं चाहिए, फिर से कॉल क्यों किया?",
]
assert len(NATIVE) == len(CASES)

# Extra tricky native-script cases (insisting is not confusion; repeats; mixed script).
EXTRA = [
    ("फिर से पूछ रहा हूँ, प्राइस बताओ वरना फोन रख दो", {"confused": 0, "frustrated": 1, "interested": 1}),
    ("फिर से बोलिए, आवाज़ नहीं आई", {"confused": 1}),
    ("पांच मिनट बाद कॉल करो, अभी कस्टमर है", {"rushed": 1}),
    ("हाँ हाँ बताइए, ऑर्डर कैसे आएंगे?", {"interested": 1, "rushed": 0}),
    ("मुझे गुजराती में बात करनी है", {"language": "hindi"}),
    ("मेरे बेटे से बात करो, वही देखता है ये सब", {"frustrated": 0, "confused": 0}),
]

NATIVE_CUES = {
    "rushed": " Native script examples: 'बिज़ी हूँ', 'जल्दी बोलो', 'बाद में कॉल करो', 'टाइम नहीं है', 'मीटिंग में हूँ', 'पांच मिनट बाद', 'சீக்கிரம்', 'પછી વાત કરું'.",
    "frustrated": " Native script examples: 'कितनी बार कॉल करोगे', 'परेशान कर दिया', 'फालतू कॉल', 'दिमाग मत खाओ', 'बंद करो', 'फिर से कॉल क्यों किया', 'वरना फोन रख दो'.",
    "confused": " Native script examples: 'समझ नहीं आया', 'क्या बोला', 'क्या मतलब', 'किस चीज़ का कॉल', 'आवाज़ नहीं आई', 'புரியல', 'સમજાયું નહીં'. 'फिर से' alone is NOT confusion when the seller is repeating a demand (e.g., 'फिर से पूछ रहा हूँ, प्राइस बताओ').",
    "bot_question": " Native script examples: 'बॉट हो क्या', 'रिकॉर्डेड कॉल', 'इंसान से बात कराओ', 'मशीन'.",
    "interested": " Native script examples: 'कितना चार्ज है', 'कब आएंगे', 'डिटेल्स भेज दो', 'ऑर्डर कैसे आएंगे', 'કેટલા પૈસા'.",
}


def questions_native():
    q = copy.deepcopy(QUESTIONS)
    for k, extra in NATIVE_CUES.items():
        q[k]["criteria"]["true"] += extra
    q["language"]["instructions"] = "Which language is the latest seller turn mainly in? Text may be in Devanagari, Tamil, Gujarati or Latin script."
    q["language"]["criteria"]["hinglish"] = "Hindi mixed with English words (often English words written in Devanagari, e.g. 'मीटिंग', 'डिटेल्स')"
    q["language"]["criteria"]["tamil"] = "Tamil, in Tamil script or romanized"
    q["language"]["criteria"]["gujarati"] = "Gujarati, in Gujarati script or romanized"
    return q


def run(cases, questions):
    jev_spike.QUESTIONS = questions
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda c: (c, jev_spike.decide(c[0])), cases))
    agree, lat, misses = {}, [], []
    for (utt, exp), (ms, js) in res:
        lat.append(ms)
        a = js["answers"]
        for k, v in exp.items():
            g = a[k]["noul"] if a[k]["type"] == "noul" else a[k]["choice"]
            ok = (g >= 0.5) == bool(v) if isinstance(v, int) else g == v
            agree.setdefault(k, [0, 0]); agree[k][0] += ok; agree[k][1] += 1
            if not ok:
                misses.append(f"{utt[:40]} | {k}: want {v} got {round(g, 2) if isinstance(g, float) else g}")
    total = sum(a for a, _ in agree.values()), sum(n for _, n in agree.values())
    return {"agree": {k: f"{a}/{n}" for k, (a, n) in agree.items()}, "total": f"{total[0]}/{total[1]}",
            "p50_ms": round(statistics.median(lat)), "misses": misses}


def main():
    native_cases = [(n, exp) for n, (_, exp) in zip(NATIVE, CASES)]
    out = {
        "A_romanized_current": run(CASES, QUESTIONS),
        "B_native_current": run(native_cases, QUESTIONS),
        "C_native_nativecues": run(native_cases, questions_native()),
        "D_extra_current": run(EXTRA, QUESTIONS),
        "E_extra_nativecues": run(EXTRA, questions_native()),
    }
    for k, v in out.items():
        print(f"\n== {k}: total {v['total']}  p50 {v['p50_ms']} ms\n   per signal {v['agree']}")
        for m in v["misses"]:
            print("   MISS", m)
    path = ROOT / "outputs" / f"spike-jev-native-{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nSaved", path.name)


if __name__ == "__main__":
    main()
