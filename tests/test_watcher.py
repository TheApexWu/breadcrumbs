"""Change-stream watcher against a live replica set (skipped without one).

    MONGO_URI="mongodb://127.0.0.1:27078/?replicaSet=rs0" python3 -m pytest tests/test_watcher.py
"""
import os
import threading
import time

import pytest
from pymongo import MongoClient

from agent.swarm import watch_change_stream

URI = os.environ.get("MONGO_URI", "")
pytestmark = pytest.mark.skipif("replicaSet" not in URI, reason="needs MONGO_URI to a replica set")


@pytest.fixture
def db():
    client = MongoClient(URI, serverSelectionTimeoutMS=2000)
    d = client["bc_watcher_test"]
    client.drop_database(d.name)
    yield d
    client.drop_database(d.name)


def insert_soon(coll, docs, delay=0.5):
    def go():
        time.sleep(delay)
        for doc in docs:
            coll.insert_one(doc)
    threading.Thread(target=go, daemon=True).start()


def test_timeout_is_honored(db):
    t = time.monotonic()
    r = watch_change_stream(lambda _: None, db=db, timeout_s=2)
    assert r["status"] == "timeout" and 1.5 < time.monotonic() - t < 5


def test_restart_picks_up_inserts_made_while_down(db):
    seen = []
    insert_soon(db.recalls, [{"recall_number": "A"}])
    watch_change_stream(lambda r: seen.append(r["recall_number"]), db=db, timeout_s=2)
    db.recalls.insert_one({"recall_number": "B"})  # watcher is down
    watch_change_stream(lambda r: seen.append(r["recall_number"]), db=db, timeout_s=2)
    assert seen == ["A", "B"]


def test_handler_error_propagates_and_insert_is_redelivered(db):
    def boom(_):
        raise ValueError("handler bug")
    insert_soon(db.recalls, [{"recall_number": "A"}])
    with pytest.raises(ValueError):
        watch_change_stream(boom, db=db, timeout_s=3)
    seen = []
    watch_change_stream(lambda r: seen.append(r["recall_number"]), db=db, timeout_s=2)
    assert seen == ["A"]


def test_standalone_mongod_reports_unavailable():
    uri = os.environ.get("MONGO_STANDALONE_URI")
    if not uri:
        pytest.skip("needs MONGO_STANDALONE_URI")
    d = MongoClient(uri, serverSelectionTimeoutMS=2000)["bc_watcher_test"]
    assert watch_change_stream(lambda _: None, db=d, timeout_s=1)["status"] == "unavailable"
