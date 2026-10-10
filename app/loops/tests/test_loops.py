"""Loop scripts offline: the review parser refuses bad output; Loop 1 proposes a safe, specific cue and flags gold gaps."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import loop1_propose as L  # noqa: E402
import review_call as R  # noqa: E402

GOOD = {"turns": [{"turn": 1, "seller": "x", "true_mode": "rushed", "tool_mode": "neutral", "switch_verdict": "missed"}],
        "persona_fit": {"verdict": "good"}, "hook": {"landed": True}, "qa": {"fatal": []}, "outcome_check": {}}


def test_parse_accepts_wrapped_json():
    out = json.dumps({"result": "Here it is:\n" + json.dumps(GOOD)})
    assert R.parse(out)["turns"][0]["switch_verdict"] == "missed"


def test_parse_refuses_bad_mode():
    bad = dict(GOOD, turns=[dict(GOOD["turns"][0], true_mode="angry")])
    try:
        R.parse(json.dumps(bad))
        assert False
    except ValueError:
        pass


def test_scrub_replaces_names(tmp_path):
    m = tmp_path / "map.json"
    m.write_text(json.dumps({"tokens": {"{SELLER_NAME}": ["Ravi Kumar", "Ravi"], "{COMPANY}": ["Ravi Traders"]}}))
    assert R.scrub("Ravi Kumar ji, Ravi Traders se", R.tokens_from_map(str(m))) == "{SELLER_NAME} ji, {COMPANY} se"


def _gold(tmp_path, rows):
    g = tmp_path / "gold.jsonl"
    g.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return str(g)


def _review(tmp_path, turns):
    d = tmp_path / "runs" / "r1"
    d.mkdir(parents=True)
    (d / "08_review.json").write_text(json.dumps(dict(GOOD, turns=turns), ensure_ascii=False), encoding="utf-8")
    return str(tmp_path / "runs")


def test_missed_turn_gets_specific_cue_with_gold_warning(tmp_path):
    runs = _review(tmp_path, [
        {"turn": 1, "seller": "ఇప్పుడు నేను ఆఫీసులో లేను", "true_mode": "rushed", "tool_mode": "neutral", "switch_verdict": "missed"},
        {"turn": 2, "seller": "నేను చెప్తాను", "true_mode": "neutral", "tool_mode": "neutral", "switch_verdict": "correct"}])
    out = L.propose(runs, _gold(tmp_path, [{"text": "haan boliye", "label": "neutral"}]))
    p = out["proposals"][0]["proposal"]
    assert p["action"] == "add_cue" and p["cue"] != "నేను" and "warning" in p  # not the generic word; gold gap flagged


def test_cue_that_breaks_gold_is_refused(tmp_path):
    runs = _review(tmp_path, [{"turn": 1, "seller": "haan boliye", "true_mode": "rushed", "tool_mode": "neutral",
                               "switch_verdict": "missed"}])
    out = L.propose(runs, _gold(tmp_path, [{"text": "haan boliye", "label": "neutral"}]))
    assert out["proposals"][0]["proposal"]["action"] == "none"
