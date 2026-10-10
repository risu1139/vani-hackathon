"""rule_checks.py both ways, in Hindi AND Telugu (review note 7): each check fires on a bad call and stays silent on a good one."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import rule_checks as RC  # noqa: E402


def call(turns, lang, ended="AGENT_ENDS", booked="yes", log=None):
    return {"transcript": [{"role": r, "content": c} for r, c in turns], "language_name": lang, "ended_by": ended,
            "agent_variables": {"meeting_fixed": booked}, "switch_log": log or []}


BAD_HI = call([("assistant", "आपकी category में 26 requirements आई हैं। कल मिलें?"), ("user", "कैसी requirements?"),
               ("assistant", "26 requirements हैं। कल सुबह मिलें या शाम?"), ("user", "ठीक है कल चार बजे"),
               ("assistant", "ठीक है, कल चार बजे executive मिलेंगे। धन्यवाद।")], "Hindi")
GOOD_HI = call([("assistant", "आपकी category में 26 requirements आई हैं।"), ("user", "कैसी requirements?"),
                ("assistant", "Satara से Rubber Bush की requirement है।"), ("user", "अच्छा, executive कब आएगा?"),
                ("assistant", "कल सुबह या शाम, कब ठीक रहेगा?"), ("user", "कल चार बजे"),
                ("assistant", "ठीक है, कल चार बजे। और कुछ मदद कर सकती हूँ?"), ("user", "नहीं, धन्यवाद")], "Hindi")
BAD_TE = call([("assistant", "మీ category లో 26 requirements వచ్చాయి. రేపు కలుద్దామా?"), ("user", "ఎన్ని లీడ్స్ వచ్చాయి"),
               ("assistant", "26 requirements ఉన్నాయి. రేపు ఉదయం లేదా సాయంత్రం?"), ("user", "సరే రేపు ఐదు గంటలకు"),
               ("assistant", "సరే, రేపు ఐదు గంటలకు executive వస్తారు. ధన్యవాదాలు.")], "Telugu")
GOOD_TE = call([("assistant", "మీ category లో 26 requirements వచ్చాయి."), ("user", "ఎన్ని లీడ్స్ వచ్చాయి"),
                ("assistant", "Satara నుండి ఒక requirement ఉంది."), ("user", "సరే రేపు ఐదు గంటలకు రండి"),
                ("assistant", "సరే, రేపు ఐదు గంటలకు. ఇంకేమైనా సహాయం కావాలా?"), ("user", "లేదు, ధన్యవాదాలు")], "Telugu")


def test_bad_calls_fail_every_auto_rule():
    for c in (BAD_HI, BAD_TE):
        r = RC.check(c)
        assert [r[k]["result"] for k in ("R2", "R3", "R5")] == ["fail", "fail", "fail"], r


def test_good_calls_pass():
    for c in (GOOD_HI, GOOD_TE):
        r = RC.check(c)
        assert [r[k]["result"] for k in ("R2", "R3", "R5")] == ["pass", "pass", "pass"], r


def test_r5_exceptions():
    assert RC.check(call([("assistant", "x"), ("user", "call mat karo")], "Hindi", log=[{"to": "opt_out"}]))["R5"]["result"] == "pass"
    assert RC.check(call([("assistant", "x"), ("user", "bye")], "Hindi", ended="USER_ENDS"))["R5"]["result"] == "pass"


def test_uncovered_language_is_unknown_not_pass():
    r = RC.check(call([("assistant", "x"), ("user", "y")], "Odia"))
    assert r["R5"]["result"] == "unknown" and r["R2"]["result"] == "unknown"
