import unittest.mock
from multiprocessing.pool import ThreadPool


import notanorm
import pytest
from atakama import ProfileInfo, ApprovalRequest

from tests.test_time_range import local_parse

from policy_basics.per_profile_throttle import (
    ProfileThrottleRule,
    ProfileThrottleDb,
    ProfileCount,
)
from policy_basics.simple_db import FileDb


def set_time(timer, iso):
    timer.now.return_value = local_parse(iso)
    timer.time.return_value = local_parse(iso).timestamp()


@pytest.mark.parametrize("persistent", [True, False])
def test_profile_throttle(persistent):
    pr = ProfileThrottleRule({"per_day": 3, "per_hour": 1, "persistent": persistent})
    pr.clear_quota(ProfileInfo(profile_id=b"pid", profile_words=[]))
    with unittest.mock.patch("policy_basics.per_profile_throttle.Timer") as timer:
        # fixed time
        set_time(timer, "2022-03-09 17:00Z")

        # same hour
        assert pr._approve_profile_request(b"pid")
        assert not pr._approve_profile_request(b"pid")

        # new hour
        set_time(timer, "2022-03-09 18:00Z")

        # 3rd req ok for the day
        assert pr._approve_profile_request(b"pid")

        # not 4th
        assert not pr._approve_profile_request(b"pid")

        # new day
        set_time(timer, "2022-03-10 00:00Z")
        assert pr._approve_profile_request(b"pid")

        # top level
        assert pr.approve_request(
            ApprovalRequest(
                request_type=None,
                device_id=b"pid",
                profile=ProfileInfo(profile_id=b"pid", profile_words=[]),
                auth_meta=None,
            )
        )


def test_persistent():
    pr = ProfileThrottleRule({"per_day": 3, "persistent": True})
    pr.clear_quota(ProfileInfo(profile_id=b"pid", profile_words=[]))

    assert pr._approve_profile_request(b"pid")
    assert pr._approve_profile_request(b"pid")
    assert pr._approve_profile_request(b"pid")
    pr = ProfileThrottleRule({"per_day": 3, "persistent": True})
    assert not pr._approve_profile_request(b"pid")


@pytest.mark.parametrize("persistent", [0, 1])
def test_throttle_db_atomic(tmp_path, persistent):
    if persistent:
        db = ProfileThrottleDb({"persistent": True, "db-file": tmp_path / "quote.db"})
    else:
        db = ProfileThrottleDb({"persistent": False})

    thread_pool = ThreadPool(10)

    cnt = 100

    def sets(_):
        return db.increment(b"pid").day_cnt

    assert all(ok for ok in thread_pool.map(sets, range(cnt)))

    assert db.get(b"pid").day_cnt == cnt


def test_throttle_db_corruption(tmp_path):
    # resilient to file corruption, just resets counts
    path = tmp_path / "quote.db"
    with path.open("w") as db_fh:
        db_fh.write("junk")
    db = ProfileThrottleDb({"persistent": True, "db-file": path})
    assert db.increment(b"pid").day_cnt == 1


def test_throttle_db_schema_bad(tmp_path):
    # resilient to schema changes, just resets counts
    path = tmp_path / "quote.db"
    with notanorm.SqliteDb(str(path)) as db:
        db.query("create table %s (ajunk, bjunk)" % FileDb.TABLE_NAME)
    db = ProfileThrottleDb({"persistent": True, "db-file": path})
    assert db.increment(b"pid").day_cnt == 1


@pytest.fixture()
def throt_db(tmp_path):
    path = tmp_path / "quote.db"
    db = ProfileThrottleDb({"persistent": True, "db-file": path})
    yield db


def test_throttle_db_weird_data(throt_db):
    bad_dct = {"tm": None, "hr": "wot", "dy": 3}
    assert throt_db.increment(b"pid").day_cnt == 1
    throt_db.db.set(
        ProfileThrottleDb._bytes_to_str(b"pid"), ProfileCount._dict_to_str(bad_dct)
    )
    assert throt_db.increment(b"pid").day_cnt == 1


def test_throttle_db_schema_change(throt_db):
    bad_dct = {"tim": 1, "hr": 1, "dy": 3}
    assert throt_db.increment(b"pid").day_cnt == 1
    throt_db.db.set(
        ProfileThrottleDb._bytes_to_str(b"pid"), ProfileCount._dict_to_str(bad_dct)
    )
    assert throt_db.increment(b"pid").day_cnt == 1
