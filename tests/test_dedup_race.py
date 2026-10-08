"""Concurrent runs on one recall must send exactly one alert (needs a loaded replica set).

    MONGO_URI="mongodb://127.0.0.1:27078/?replicaSet=rs0" python3 -m pytest tests/test_dedup_race.py
"""
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

URI = os.environ.get("MONGO_URI", "")
pytestmark = pytest.mark.skipif("replicaSet" not in URI, reason="needs MONGO_URI to a loaded replica set")

HERO = "F-0757-2022"
RUNS = 8


@pytest.fixture
def swarm_db():
    os.environ.pop("OPENROUTER_API_KEY", None)
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    from agent import swarm
    from db.queries import get_db
    from sim.operator import build_portfolio
    db = get_db()
    build_portfolio(db)
    db.agent_memory.drop()
    return swarm, db


def test_concurrent_runs_send_one_alert(swarm_db):
    swarm, db = swarm_db
    adapter = swarm.ModelAdapter(backend="openrouter")
    with ThreadPoolExecutor(RUNS) as ex:
        outs = list(ex.map(lambda _: swarm.run(HERO, db=db, adapter=adapter), range(RUNS)))
    sent = [o for o in outs if not o["deduped"]]
    assert len(sent) == 1, "%d of %d concurrent runs sent an alert" % (len(sent), RUNS)
    assert swarm.alert_count(HERO, db) == 1


def test_forced_realert_is_still_allowed(swarm_db):
    swarm, db = swarm_db
    adapter = swarm.ModelAdapter(backend="openrouter")
    swarm.run(HERO, db=db, adapter=adapter)
    out = swarm.run(HERO, db=db, adapter=adapter, force_alert=True)
    assert out["deduped"] is False


def test_stale_claim_is_taken_over_fresh_one_is_not(swarm_db):
    swarm, db = swarm_db
    first = swarm.claim_alert("R-STALE", db)
    assert swarm.claim_alert("R-STALE", db) is None  # live claim: someone is sending
    db.agent_memory.update_one({"_id": first["_id"]}, {"$set": {"ts": "2000-01-01T00:00:00Z"}})
    taken = swarm.claim_alert("R-STALE", db)
    assert taken is not None and taken["run_id"] != first["run_id"]


def test_completed_claim_is_never_taken_over(swarm_db):
    swarm, db = swarm_db
    claim = swarm.claim_alert("R-DONE", db)
    swarm.record_run("R-DONE", "alert sent", True, {}, db=db, claim=claim, sent_ok=True)
    db.agent_memory.update_one({"_id": claim["_id"]}, {"$set": {"ts": "2000-01-01T00:00:00Z"}})
    assert swarm.claim_alert("R-DONE", db) is None


def test_alert_recorded_before_claims_existed_is_honored(swarm_db):
    swarm, db = swarm_db
    db.agent_memory.insert_one({"recall_id": "R-LEGACY", "alert_sent": 1, "re_alert": False})
    assert swarm.claim_alert("R-LEGACY", db) is None
