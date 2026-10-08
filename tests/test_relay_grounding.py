"""The /ask relay flags figures the model did not get from the recall facts. No network."""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import telegram_relay as relay  # noqa: E402

FACTS = ("FDA recall F-0757-2022: DOLE FRESH VEGETABLES INC Class I. EXPOSED SITES: 5 of the "
         "operator's 12 locations. 3 have prior critical DOHMH violations. Distributor DOLE: "
         "4 Class-I recalls of 1,204 total.")


def fake_model(answer, monkeypatch):
    body = json.dumps({"choices": [{"message": {"content": "<think>x</think>" + answer}}]}).encode()
    monkeypatch.setattr(relay.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(body))


def test_grounded_answer_passes_untouched(monkeypatch):
    fake_model("5 of your 12 sites are exposed, and 3 have critical violations.", monkeypatch)
    r = relay._ask("how many sites?", FACTS)
    assert r["ungrounded"] == [] and "unverified" not in r["answer"]


def test_invented_number_is_flagged_in_the_answer(monkeypatch):
    fake_model("7 sites are exposed.", monkeypatch)
    r = relay._ask("how many sites?", FACTS)
    assert r["ungrounded"] == ["7"] and r["answer"].endswith("[unverified: 7 not in the recall facts]")


def test_thousands_separator_and_sentence_period_still_match():
    assert relay._ungrounded_numbers("1204 recalls total, 5.", FACTS) == []


def test_prompt_no_longer_forbids_saying_unknown():
    src = Path(relay.__file__).read_text()
    assert "never say \"'not specified'" not in src and "count them yourself" not in src
