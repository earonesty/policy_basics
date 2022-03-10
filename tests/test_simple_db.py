import functools

import pytest

from policy_basics.simple_db import FileDb, MemoryDb


@pytest.mark.parametrize("persistent", [0, 1])
def test_simple_db(tmp_path, persistent):
    if persistent:
        db = FileDb(tmp_path / "quote.db")
    else:
        db = MemoryDb()

    db.set("key", 32)
    assert db.get("key") == 32
    from multiprocessing.pool import ThreadPool

    p = ThreadPool(10)

    def sets(i):
        db.set(i, i)
        return db.get(i)

    def sum(a, b):
        return a + b

    res = functools.reduce(sum, p.map(sets, range(100)))
    reg = functools.reduce(sum, range(100))

    assert res == reg

    assert db.get(4) == 4
    db.remove(4)
    assert db.get(4) is None

    assert db.get(5) == 5
    db.clear()
    assert all(db.get(i) is None for i in range(100))
