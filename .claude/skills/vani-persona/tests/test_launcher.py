"""run_persona.py end to end with a stub CLI (plan §5a items 6, 10, 11): the good path compiles; the bypass and every
fail-closed case end in status=error with a reason and NO Sarvam variables; the self-test catches dead hooks."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(__file__)
LAUNCHER = os.path.join(HERE, "..", "run_persona.py")
STUB = os.path.join(HERE, "stub_claude.py")


def seller(tmp, dnc=False):
    d = tmp / "export"
    (d / "calls").mkdir(parents=True)
    pts = {"H02": {"value": {"vertical_name": "NSD Top Cities"}}, "B01": {"value": {"seller_city": "Hyderabad", "seller_state": "Telangana"}}}
    if dnc:
        pts["X00"] = {"value": {"seller_flags": {"do_not_call_requested": 1}}}
    (d / "context.json").write_text(json.dumps({"points": pts}), encoding="utf-8")
    (d / "INDEX.md").write_text("# INDEX\n- **K1** Division: NSD\n", encoding="utf-8")
    (d / "core.md").write_text("# core\n### A07 Gender / salutation\nnone\n### B01 City\nHyderabad, Telangana\n### B03 Languages\nTelugu\n", encoding="utf-8")
    return d


def launch(tmp, mode, dnc=False, timeout=None):
    env = dict(os.environ, VANI_CLAUDE=STUB, STUB_MODE=mode, VANI_SCOREBOARDS=str(tmp / "boards"),
               VANI_LAUNCHER_DIR=str(tmp / "launcher"), PYTHONIOENCODING="utf-8")
    env.pop("VANI_HIERARCHY", None)
    args = [sys.executable, LAUNCHER, "--folder", str(seller(tmp, dnc)), "--runs", str(tmp / "runs"), "--decision-id", f"t-{mode}"]
    if timeout:
        args += ["--timeout", str(timeout)]
    r = subprocess.run(args, env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
    run = tmp / "runs" / f"t-{mode}"
    st = json.loads((run / "status.json").read_text(encoding="utf-8"))
    return r, st, run


def no_vars(run):
    return not (run / "05_sarvam_vars.json").exists() and not (run / "06_sarvam_prompt.md").exists()


def test_good_path_compiles(tmp_path):
    r, st, run = launch(tmp_path, "good")
    assert st["status"] == "done", st
    assert st["selftest"] == "pass" and st["validation"] == "pass"
    assert (run / "05_sarvam_vars.json").exists() and r.returncode == 0


@pytest.mark.parametrize("mode,why", [
    ("bypass", "no finalize"),                 # item 10: hand-written persona, gate never saw it
    ("edit", "differ from the finalize sha"),  # edited after finalize
    ("tamper", "01_facts.json or 03_prior.json changed"),
    ("editskill", "skill copy changed"),       # e.g. the validator weakened
    ("sellerchange", "seller copy changed"),
    ("noop", "agent turn"),                    # claude produced nothing
    ("crash", "agent turn"),
    ("wrongmodel", "model check"),
    ("dead_hooks", "self-test"),               # a CLI update silenced the hooks
])
def test_fail_closed(tmp_path, mode, why):
    r, st, run = launch(tmp_path, mode)
    assert st["status"] == "error" and why in st["reason"], st
    assert no_vars(run) and r.returncode == 0


def test_killed_mid_turn(tmp_path):
    r, st, run = launch(tmp_path, "hang", timeout=5)
    assert st["status"] == "error" and no_vars(run)


def test_do_not_call_from_facts_not_from_agent(tmp_path):
    r, st, run = launch(tmp_path, "dnc", dnc=True)
    assert st["status"] == "do_not_call" and no_vars(run)


def test_agent_says_dnc_but_facts_do_not(tmp_path):
    r, st, run = launch(tmp_path, "dnc", dnc=False)
    assert st["status"] == "error" and no_vars(run)


def test_dnc_with_persona_written(tmp_path):
    """Review fix 6: the agent cannot delete files, so the launcher discards the persona; still no call."""
    r, st, run = launch(tmp_path, "dnc_persona", dnc=True)
    assert st["status"] == "do_not_call" and "discarded" in st["reason"] and no_vars(run)
    assert not (run / "04_persona.json").exists() and (run / "04_persona.discarded.json").exists()


def test_forged_ledger_still_fails_on_content(tmp_path):
    """Review fix 4: an INVALID hand-written persona + a forged finalize row with matching shas -> the validator fails it."""
    r, st, run = launch(tmp_path, "forged")
    assert st["status"] == "error" and "validator" in st["reason"] and no_vars(run)
