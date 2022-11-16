# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

import functools
from multiprocessing.pool import ThreadPool

import pytest

from policy_basics.simple_db import UriDb, MemoryDb


@pytest.mark.parametrize("persistent", [0, 1])
def test_simple_db(tmp_path, persistent):
    if persistent:
        db = UriDb(tmp_path / "quote.db")
    else:
        db = MemoryDb()

    db.set("key", 32)
    assert db.get("key") == 32

    db.set("key", "val")
    assert db.get("key") == "val"

    tpool = ThreadPool(10)

    def sets(i):
        db.set(i, i)
        return db.get(i)

    def _sum(a, b):
        return a + b

    res = functools.reduce(_sum, tpool.map(sets, range(100)))
    reg = functools.reduce(_sum, range(100))

    assert res == reg

    assert db.get(4) == 4
    db.remove(4)
    assert db.get(4) is None

    assert db.get(5) == 5
    db.clear()
    assert all(db.get(i) is None for i in range(100))
