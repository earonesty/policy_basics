import abc
import typing

import notanorm

DbVal = typing.Union[str, int, None]

__autodoc__ = False


class AbstractDb(abc.ABC):
    """Simple abstract get/set class."""

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


class FileDb(AbstractDb):
    """File based db."""

    TABLE_NAME = "vals"
    TEST_KEY = "^ufhvG6xWsMtTBkHhQQ+cZg!"

    def __init__(self, path):
        self.path = str(path)
        try:
            self.db = None
            self.db = notanorm.SqliteDb(self.path)
            self.db.query(
                "create table if not exists %s (key primary key, val)"
                % FileDb.TABLE_NAME,
            )
            self.__check_ok()
        except Exception:
            # close db if we fail to verify that it works
            self.db and self.db.close()
            raise

    def __check_ok(self):
        self.db.upsert(FileDb.TABLE_NAME, key=FileDb.TEST_KEY, val=44)
        assert self.db.select_one(FileDb.TABLE_NAME, key=FileDb.TEST_KEY).val == 44
        self.db.delete(FileDb.TABLE_NAME, key=FileDb.TEST_KEY)

    def set(self, key, val):
        self.db.upsert(FileDb.TABLE_NAME, key=key, val=val)

    def get(self, key):
        ret = self.db.select_one(FileDb.TABLE_NAME, key=key)
        if ret is None:
            return None
        return ret.val

    def clear(self):
        self.db.delete_all(FileDb.TABLE_NAME)

    def remove(self, key):
        self.db.delete(FileDb.TABLE_NAME, key=key)


class MemoryDb(AbstractDb):
    """In memory db."""

    def __init__(self):
        self.db = {}

    def set(self, key, val):
        self.db[key] = val

    def get(self, key):
        return self.db.get(key, None)

    def clear(self):
        self.db = {}

    def remove(self, key):
        self.db.pop(key, None)
