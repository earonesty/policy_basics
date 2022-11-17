# SPDX-FileCopyrightText: © Atakama, Inc <support@atakama.com>
# SPDX-License-Identifier: LGPL-3.0-or-later

import abc
import typing

import notanorm

DbVal = typing.Union[str, int, None]

__autodoc__ = False


class AbstractDb(abc.ABC):
    """Simple abstract get/set class."""

    _connected = False

    def connect(self):
        if not self._connected:
            self._connect()
        self._connected = True

    def _connect(self):
        ...

    @abc.abstractmethod
    def set(self, key, value: DbVal):
        ...

    @abc.abstractmethod
    def get(self, key) -> typing.Optional[DbVal]:
        ...

    @abc.abstractmethod
    def clear(self):
        ...

    @abc.abstractmethod
    def remove(self, key):
        ...


class UriDb(AbstractDb):
    """File based db."""

    TABLE_NAME = "vals"
    TEST_KEY = "^ufhvG6xWsMtTBkHhQQ+cZg!"

    def __init__(self, path=None, *, uri=None, table=TABLE_NAME):
        assert not (path and uri), "one of path or uri, not both"

        if path:
            uri = "sqlite:" + str(path)

        self.uri = uri
        self.table = table
        self.db = None

        self.connect()

    def _connect(self):
        self.db = None
        try:
            self.db = notanorm.open_db(self.uri)

            if self.db.uri_name == "sqlite":
                self.db.execute("PRAGMA journal_mode=WAL;")
                self.db.execute("PRAGMA synchronous=NORMAL;")

            self.db.execute_ddl(
                "create table %s (key varchar(64) primary key, val text, ival integer)"
                % self.table,
                "mysql",
            )

            self.__check_ok()
        except Exception:
            # close db if we fail to verify that it works
            if self.db:
                self.db.close()
            raise

    def __check_ok(self):
        self.db.upsert(self.table, key=UriDb.TEST_KEY, ival=44)
        assert self.db.select_one(self.table, key=UriDb.TEST_KEY).ival == 44
        self.db.delete(self.table, key=UriDb.TEST_KEY)

    def set(self, key, value: DbVal):
        # for speed, we do an unidiomatic type check
        if type(value) is str:  # pylint: disable=unidiomatic-typecheck
            self.db.upsert(self.table, key=key, val=value, ival=None)
        else:
            self.db.upsert(self.table, key=key, ival=value, val=None)

    def get(self, key) -> DbVal:
        ret = self.db.select_one(self.table, key=key)
        if ret is None:
            return None
        return ret.ival if ret.val is None else ret.val

    def clear(self):
        self.db.delete_all(self.table)

    def remove(self, key):
        self.db.delete(self.table, key=key)


class MemoryDb(AbstractDb):
    """In memory db."""

    def __init__(self):
        self.db = {}

    def set(self, key, value):
        self.db[key] = value

    def get(self, key):
        return self.db.get(key, None)

    def clear(self):
        self.db = {}

    def remove(self, key):
        self.db.pop(key, None)
